#!/usr/bin/env php
<?php

function line_count_for_content(string $content): int {
    return max(1, substr_count($content, "\n") + 1);
}

function code_line_count_for_content(string $content): int {
    $count = 0;
    foreach (explode("\n", $content) as $line) {
        $trimmed = trim($line);
        if ($trimmed !== '' && !str_starts_with($trimmed, '//') && !str_starts_with($trimmed, '#') && !str_starts_with($trimmed, '/*') && !str_starts_with($trimmed, '*')) {
            $count++;
        }
    }
    return $count;
}

function token_line_value($token, int $fallbackLine): int {
    return is_array($token) ? $token[2] : $fallbackLine;
}

function token_text($token): string {
    return is_array($token) ? $token[1] : $token;
}

function normalize_namespace_reference(string $value): string {
    return trim(str_replace('/', '\\', $value), " \\");
}

function normalize_import_path(string $value): string {
    return trim(str_replace('\\', '/', $value), '/ ');
}

function import_parent_path(string $value): string {
    $normalizedPath = normalize_import_path($value);
    $parts = explode('/', $normalizedPath);
    array_pop($parts);
    return implode('/', $parts);
}

function is_name_token($token): bool {
    if (!is_array($token)) {
        return false;
    }

    $tokenId = $token[0];
    $valid = [T_STRING];
    if (defined('T_NS_SEPARATOR')) {
        $valid[] = T_NS_SEPARATOR;
    }
    if (defined('T_NAME_QUALIFIED')) {
        $valid[] = T_NAME_QUALIFIED;
    }
    if (defined('T_NAME_FULLY_QUALIFIED')) {
        $valid[] = T_NAME_FULLY_QUALIFIED;
    }
    if (defined('T_NAME_RELATIVE')) {
        $valid[] = T_NAME_RELATIVE;
    }

    return in_array($tokenId, $valid, true);
}

function use_import_entry(string $usePath, bool $isAliased, int $statementId, bool $usesJoinedImport): array {
    $normalizedUsePath = normalize_namespace_reference($usePath);
    return [
        'path' => $normalizedUsePath,
        'is_relative' => false,
        'normalized_path' => normalize_import_path($normalizedUsePath),
        'imported_name' => '',
        'is_aliased' => $isAliased,
        'crossing_type' => 'symbol',
        'file_barrier_crossed' => true,
        'statement_id' => $statementId,
        'join_key' => import_parent_path($normalizedUsePath),
        'uses_joined_import' => $usesJoinedImport,
    ];
}

function use_statement_imports(array $tokens, int $useIndex, int $statementId): array {
    $count = count($tokens);
    $j = $useIndex + 1;
    $prefix = '';
    $imports = [];

    while ($j < $count && token_text($tokens[$j]) !== ';') {
        $token = $tokens[$j];
        if ($token === '{') {
            $j++;
            $name = '';
            $isAliased = false;
            while ($j < $count && token_text($tokens[$j]) !== '}') {
                $current = $tokens[$j];
                if ($current === ',') {
                    if ($name !== '') {
                        $imports[] = use_import_entry(
                            rtrim($prefix, '\\') . '\\' . $name,
                            $isAliased,
                            $statementId,
                            true
                        );
                    }
                    $name = '';
                    $isAliased = false;
                } elseif (is_array($current) && $current[0] === T_AS) {
                    $isAliased = true;
                    while ($j < $count && token_text($tokens[$j]) !== ',' && token_text($tokens[$j]) !== '}') {
                        $j++;
                    }
                    $j--;
                } elseif (is_name_token($current)) {
                    $name .= token_text($current);
                }
                $j++;
            }
            if ($name !== '') {
                $imports[] = use_import_entry(rtrim($prefix, '\\') . '\\' . $name, $isAliased, $statementId, true);
            }
            return $imports;
        }
        if ($token === ',') {
            if ($prefix !== '') {
                $imports[] = use_import_entry($prefix, false, $statementId, false);
            }
            $prefix = '';
        } elseif (is_array($token) && $token[0] === T_AS) {
            if ($prefix !== '') {
                $imports[] = use_import_entry($prefix, true, $statementId, false);
            }
            while ($j < $count && token_text($tokens[$j]) !== ',' && token_text($tokens[$j]) !== ';') {
                $j++;
            }
            $prefix = '';
            continue;
        } elseif (is_name_token($token)) {
            $prefix .= token_text($token);
        }
        $j++;
    }

    if ($prefix !== '') {
        $imports[] = use_import_entry($prefix, false, $statementId, false);
    }

    return $imports;
}

function member_visibility(array $tokens, int $functionIndex): string {
    for ($index = $functionIndex - 1; $index >= 0; $index--) {
        $token = $tokens[$index];
        if (!is_array($token)) {
            $text = token_text($token);
            if ($text === ';' || $text === '{' || $text === '}') {
                break;
            }
            continue;
        }

        $tokenId = $token[0];
        if (in_array($tokenId, [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT, T_STATIC, T_FINAL, T_ABSTRACT], true)) {
            continue;
        }
        if ($tokenId === T_PRIVATE) {
            return 'private';
        }
        if ($tokenId === T_PROTECTED) {
            return 'protected';
        }
        if ($tokenId === T_PUBLIC) {
            return 'public';
        }
        break;
    }

    return 'public';
}

function visibility_intent(string $name, string $visibility): string {
    $magicMethods = [
        '__call',
        '__callStatic',
        '__clone',
        '__construct',
        '__debugInfo',
        '__destruct',
        '__get',
        '__invoke',
        '__isset',
        '__serialize',
        '__set',
        '__set_state',
        '__sleep',
        '__toString',
        '__unserialize',
        '__unset',
        '__wakeup',
    ];
    if (in_array($name, $magicMethods, true)) {
        return $visibility;
    }
    if (str_starts_with($name, '__')) {
        return 'private';
    }
    if (str_starts_with($name, '_')) {
        return 'protected';
    }
    return $visibility;
}

function find_block_end_line(array $tokens, int $startIndex, int $fallbackLine): int {
    $depth = 0;
    $seenBrace = false;
    $currentLine = $fallbackLine;
    $count = count($tokens);

    for ($index = $startIndex; $index < $count; $index++) {
        $token = $tokens[$index];
        $currentLine = token_line_value($token, $currentLine);
        $text = token_text($token);

        if ($text === '{') {
            $depth++;
            $seenBrace = true;
            continue;
        }
        if ($text === '}') {
            if ($seenBrace) {
                $depth--;
                if ($depth === 0) {
                    return $currentLine;
                }
            }
            continue;
        }
        if (!$seenBrace && $text === ';') {
            return $currentLine;
        }
    }

    return $currentLine;
}

function find_parameter_bounds(array $tokens, int $functionIndex): array {
    $count = count($tokens);
    $openIndex = null;

    for ($index = $functionIndex; $index < $count; $index++) {
        $text = token_text($tokens[$index]);
        if ($text === '(') {
            $openIndex = $index;
            break;
        }
        if ($text === ';' || $text === '{') {
            return [null, null];
        }
    }

    if ($openIndex === null) {
        return [null, null];
    }

    $depth = 0;
    for ($index = $openIndex; $index < $count; $index++) {
        $text = token_text($tokens[$index]);
        if ($text === '(') {
            $depth++;
            continue;
        }
        if ($text === ')') {
            $depth--;
            if ($depth === 0) {
                return [$openIndex, $index];
            }
        }
    }

    return [$openIndex, null];
}

function parameter_counts(array $tokens, ?int $openIndex, ?int $closeIndex): array {
    if ($openIndex === null || $closeIndex === null || $closeIndex <= $openIndex + 1) {
        return ['declared_args' => 0, 'optional_args' => 0];
    }

    $declaredArgs = 0;
    $optionalArgs = 0;
    $segmentHasVariable = false;
    $segmentIsOptional = false;
    $depth = 0;

    $flushSegment = function () use (&$declaredArgs, &$optionalArgs, &$segmentHasVariable, &$segmentIsOptional): void {
        if ($segmentHasVariable) {
            $declaredArgs++;
            if ($segmentIsOptional) {
                $optionalArgs++;
            }
        }
        $segmentHasVariable = false;
        $segmentIsOptional = false;
    };

    for ($index = $openIndex + 1; $index < $closeIndex; $index++) {
        $token = $tokens[$index];
        $text = token_text($token);

        if ($text === '(' || $text === '[' || $text === '{') {
            $depth++;
            continue;
        }
        if ($text === ')' || $text === ']' || $text === '}') {
            $depth = max(0, $depth - 1);
            continue;
        }
        if ($text === ',' && $depth === 0) {
            $flushSegment();
            continue;
        }
        if (is_array($token) && $token[0] === T_VARIABLE) {
            $segmentHasVariable = true;
            continue;
        }
        if ($text === '=' && $depth === 0) {
            $segmentIsOptional = true;
            continue;
        }
        if ($text === '...') {
            $segmentIsOptional = true;
        }
    }

    $flushSegment();

    return ['declared_args' => $declaredArgs, 'optional_args' => $optionalArgs];
}

function is_visibility_token($token): bool {
    return is_array($token) && in_array($token[0], [T_PUBLIC, T_PROTECTED, T_PRIVATE], true);
}

function add_class_property(array &$classDefinition, string $name, bool $isOptional): void {
    foreach ($classDefinition['properties'] as &$property) {
        if ($property['name'] === $name) {
            $property['is_optional'] = $property['is_optional'] || $isOptional;
            return;
        }
    }
    unset($property);

    $classDefinition['properties'][] = [
        'name' => $name,
        'is_optional' => $isOptional,
    ];
}

function split_top_level_segments(array $tokens, int $startIndex, int $endIndex): array {
    $segments = [];
    $segmentStart = $startIndex;
    $depth = 0;
    for ($index = $startIndex; $index < $endIndex; $index++) {
        $text = token_text($tokens[$index]);
        if ($text === '(' || $text === '[' || $text === '{') {
            $depth++;
            continue;
        }
        if ($text === ')' || $text === ']' || $text === '}') {
            $depth = max(0, $depth - 1);
            continue;
        }
        if ($text === ',' && $depth === 0) {
            $segments[] = array_slice($tokens, $segmentStart, $index - $segmentStart);
            $segmentStart = $index + 1;
        }
    }

    $segments[] = array_slice($tokens, $segmentStart, $endIndex - $segmentStart);
    return $segments;
}

function segment_variable_name(array $segment): ?string {
    foreach ($segment as $token) {
        if (is_array($token) && $token[0] === T_VARIABLE) {
            return ltrim($token[1], '$');
        }
    }
    return null;
}

function segment_has_visibility(array $segment): bool {
    foreach ($segment as $token) {
        if (is_visibility_token($token)) {
            return true;
        }
    }
    return false;
}

function segment_has_optional_property_type(array $segment): bool {
    foreach ($segment as $token) {
        if (is_array($token) && $token[0] === T_VARIABLE) {
            return false;
        }
        $text = strtolower(token_text($token));
        if ($text === '?' || $text === 'null') {
            return true;
        }
    }
    return false;
}

function segment_is_optional_property(array $segment, bool $baseOptional = false): bool {
    if ($baseOptional || segment_has_optional_property_type($segment)) {
        return true;
    }

    $seenVariable = false;
    $seenEquals = false;
    foreach ($segment as $token) {
        $text = strtolower(token_text($token));
        if (is_array($token) && $token[0] === T_VARIABLE) {
            $seenVariable = true;
            continue;
        }
        if ($seenVariable && $text === '=') {
            $seenEquals = true;
            continue;
        }
        if ($seenEquals && $text === 'null') {
            return true;
        }
    }
    return false;
}

function promoted_properties(array $tokens, ?int $openIndex, ?int $closeIndex): array {
    if ($openIndex === null || $closeIndex === null || $closeIndex <= $openIndex + 1) {
        return [];
    }

    $properties = [];
    foreach (split_top_level_segments($tokens, $openIndex + 1, $closeIndex) as $segment) {
        if (!segment_has_visibility($segment)) {
            continue;
        }
        $name = segment_variable_name($segment);
        if ($name === null) {
            continue;
        }
        $properties[] = [
            'name' => $name,
            'is_optional' => segment_is_optional_property($segment),
        ];
    }
    return $properties;
}

function property_declaration_properties(array $tokens, int $startIndex): array {
    $count = count($tokens);
    $endIndex = $startIndex;
    for (; $endIndex < $count; $endIndex++) {
        $token = $tokens[$endIndex];
        if (is_array($token) && $token[0] === T_FUNCTION) {
            return [];
        }
        $text = token_text($token);
        if ($text === ';' || $text === '{') {
            break;
        }
    }

    $statement = array_slice($tokens, $startIndex, $endIndex - $startIndex);
    $baseOptional = segment_has_optional_property_type($statement);
    $properties = [];
    foreach (split_top_level_segments($tokens, $startIndex, $endIndex) as $segment) {
        $name = segment_variable_name($segment);
        if ($name === null) {
            continue;
        }
        $properties[] = [
            'name' => $name,
            'is_optional' => segment_is_optional_property($segment, $baseOptional),
        ];
    }
    return $properties;
}

function previous_significant_text(array $tokens, int $index): string {
    for ($j = $index - 1; $j >= 0; $j--) {
        $token = $tokens[$j];
        if (is_array($token) && in_array($token[0], [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT], true)) {
            continue;
        }
        return token_text($token);
    }
    return '';
}

function previous_significant_token(array $tokens, int $index) {
    for ($j = $index - 1; $j >= 0; $j--) {
        $token = $tokens[$j];
        if (is_array($token) && in_array($token[0], [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT], true)) {
            continue;
        }
        return $token;
    }
    return null;
}

function class_token_is_abstract(array $tokens, int $classIndex): bool {
    $token = previous_significant_token($tokens, $classIndex);
    return is_array($token) && $token[0] === T_ABSTRACT;
}

function member_is_abstract(array $tokens, int $functionIndex): bool {
    for ($index = $functionIndex - 1; $index >= 0; $index--) {
        $token = $tokens[$index];
        if (!is_array($token)) {
            $text = token_text($token);
            if ($text === ';' || $text === '{' || $text === '}') {
                break;
            }
            continue;
        }

        if (in_array($token[0], [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT, T_PUBLIC, T_PROTECTED, T_PRIVATE, T_STATIC, T_FINAL], true)) {
            continue;
        }
        return $token[0] === T_ABSTRACT;
    }
    return false;
}

function extract_file(string $path): array {
    $content = file_get_contents($path);
    $tokens = token_get_all($content);
    $imports = [];
    $classes = [];
    $interfaces = [];
    $types = [];
    $abstractClasses = [];
    $functions = [];
    $classIndexByName = [];
    $interfaceIndexByName = [];
    $abstractClassIndexByName = [];

    $count = count($tokens);
    $currentLine = 1;
    $braceDepth = 0;
    $activeDefinitionKind = null;
    $activeDefinitionName = null;
    $activeDefinitionDepth = 0;
    $statementId = 0;

    for ($i = 0; $i < $count; $i++) {
        $token = $tokens[$i];
        $currentLine = token_line_value($token, $currentLine);

        if ($token === '{') {
            $braceDepth++;
            continue;
        }
        if ($token === '}') {
            if ($activeDefinitionName !== null && $braceDepth === $activeDefinitionDepth) {
                $activeDefinitionKind = null;
                $activeDefinitionName = null;
                $activeDefinitionDepth = 0;
            }
            $braceDepth = max(0, $braceDepth - 1);
            continue;
        }
        if (!is_array($token)) {
            continue;
        }

        if ($token[0] === T_USE) {
            $statementId++;
            $imports = array_merge(
                $imports,
                use_statement_imports($tokens, $i, $statementId),
            );
            continue;
        }

        if ($token[0] === T_CLASS) {
            $j = $i + 1;
            while ($j < $count && token_text($tokens[$j]) !== '{') {
                if (is_array($tokens[$j]) && $tokens[$j][0] === T_STRING) {
                    $className = $tokens[$j][1];
                    if (class_token_is_abstract($tokens, $i)) {
                        $abstractClasses[] = [
                            'name' => $className,
                            'visibility' => 'public',
                            'visibility_intent' => visibility_intent($className, 'public'),
                            'abstract_methods' => [],
                            'concrete_methods' => [],
                            'properties' => [],
                            'line_count' => max(
                                0,
                                find_block_end_line($tokens, $j, $currentLine) - $currentLine + 1
                            ),
                        ];
                        $abstractClassIndexByName[$className] = count($abstractClasses) - 1;
                        $activeDefinitionKind = 'abstract_class';
                    } else {
                        $classes[] = [
                            'name' => $className,
                            'visibility' => 'public',
                            'visibility_intent' => visibility_intent($className, 'public'),
                            'methods' => [],
                            'properties' => [],
                            'line_count' => max(
                                0,
                                find_block_end_line($tokens, $j, $currentLine) - $currentLine + 1
                            ),
                        ];
                        $classIndexByName[$className] = count($classes) - 1;
                        $activeDefinitionKind = 'class';
                    }
                    $activeDefinitionName = $className;
                    $activeDefinitionDepth = $braceDepth + 1;
                    break;
                }
                $j++;
            }
            continue;
        }

        if ($token[0] === T_INTERFACE) {
            $j = $i + 1;
            while ($j < $count && token_text($tokens[$j]) !== '{') {
                if (is_array($tokens[$j]) && $tokens[$j][0] === T_STRING) {
                    $interfaceName = $tokens[$j][1];
                    $interfaces[] = [
                        'name' => $interfaceName,
                        'visibility' => 'public',
                        'visibility_intent' => visibility_intent($interfaceName, 'public'),
                        'methods' => [],
                        'properties' => [],
                        'signatures' => [],
                        'line_count' => max(
                            0,
                            find_block_end_line($tokens, $j, $currentLine) - $currentLine + 1
                        ),
                    ];
                    $interfaceIndexByName[$interfaceName] = count($interfaces) - 1;
                    $activeDefinitionKind = 'interface';
                    $activeDefinitionName = $interfaceName;
                    $activeDefinitionDepth = $braceDepth + 1;
                    break;
                }
                $j++;
            }
            continue;
        }

        if (
            $activeDefinitionName !== null
            && in_array($activeDefinitionKind, ['class', 'abstract_class'], true)
            && $braceDepth === $activeDefinitionDepth
            && is_visibility_token($token)
            && !in_array(previous_significant_text($tokens, $i), ['(', ','], true)
        ) {
            $definitionIndex = $activeDefinitionKind === 'class'
                ? $classIndexByName[$activeDefinitionName]
                : $abstractClassIndexByName[$activeDefinitionName];
            foreach (property_declaration_properties($tokens, $i) as $property) {
                if ($activeDefinitionKind === 'class') {
                    add_class_property(
                        $classes[$definitionIndex],
                        $property['name'],
                        $property['is_optional']
                    );
                } else {
                    add_class_property(
                        $abstractClasses[$definitionIndex],
                        $property['name'],
                        $property['is_optional']
                    );
                }
            }
            continue;
        }

        if ($token[0] === T_FUNCTION) {
            $j = $i + 1;
            while ($j < $count && token_text($tokens[$j]) !== '(') {
                if (is_array($tokens[$j]) && $tokens[$j][0] === T_STRING) {
                    $functionName = $tokens[$j][1];
                    $lineCount = max(
                        0,
                        find_block_end_line($tokens, $j, $currentLine) - $currentLine + 1
                    );
                    [$openIndex, $closeIndex] = find_parameter_bounds($tokens, $i);
                    $parameterCounts = parameter_counts($tokens, $openIndex, $closeIndex);
                    if ($activeDefinitionKind === 'class' && $activeDefinitionName !== null && array_key_exists($activeDefinitionName, $classIndexByName)) {
                        if ($functionName === '__construct') {
                            foreach (promoted_properties($tokens, $openIndex, $closeIndex) as $property) {
                                add_class_property(
                                    $classes[$classIndexByName[$activeDefinitionName]],
                                    $property['name'],
                                    $property['is_optional']
                                );
                            }
                        }
                        $visibility = member_visibility($tokens, $i);
                        $classes[$classIndexByName[$activeDefinitionName]]['methods'][] = [
                            'name' => $functionName,
                            'visibility' => $visibility,
                            'visibility_intent' => visibility_intent($functionName, $visibility),
                            'line_count' => $lineCount,
                            'declared_args' => $parameterCounts['declared_args'],
                            'optional_args' => $parameterCounts['optional_args'],
                        ];
                    } elseif ($activeDefinitionKind === 'abstract_class' && $activeDefinitionName !== null && array_key_exists($activeDefinitionName, $abstractClassIndexByName)) {
                        if ($functionName === '__construct') {
                            foreach (promoted_properties($tokens, $openIndex, $closeIndex) as $property) {
                                add_class_property(
                                    $abstractClasses[$abstractClassIndexByName[$activeDefinitionName]],
                                    $property['name'],
                                    $property['is_optional']
                                );
                            }
                        }
                        $visibility = member_visibility($tokens, $i);
                        $methodDefinition = [
                            'name' => $functionName,
                            'visibility' => $visibility,
                            'visibility_intent' => visibility_intent($functionName, $visibility),
                            'line_count' => $lineCount,
                            'declared_args' => $parameterCounts['declared_args'],
                            'optional_args' => $parameterCounts['optional_args'],
                        ];
                        if (member_is_abstract($tokens, $i)) {
                            $abstractClasses[$abstractClassIndexByName[$activeDefinitionName]]['abstract_methods'][] = $methodDefinition;
                        } else {
                            $abstractClasses[$abstractClassIndexByName[$activeDefinitionName]]['concrete_methods'][] = $methodDefinition;
                        }
                    } elseif ($activeDefinitionKind === 'interface' && $activeDefinitionName !== null && array_key_exists($activeDefinitionName, $interfaceIndexByName)) {
                        $visibility = member_visibility($tokens, $i);
                        $interfaces[$interfaceIndexByName[$activeDefinitionName]]['methods'][] = [
                            'name' => $functionName,
                            'visibility' => $visibility,
                            'visibility_intent' => visibility_intent($functionName, $visibility),
                            'line_count' => $lineCount,
                            'declared_args' => $parameterCounts['declared_args'],
                            'optional_args' => $parameterCounts['optional_args'],
                        ];
                    } else {
                        $functions[] = [
                            'name' => $functionName,
                            'visibility' => 'public',
                            'visibility_intent' => visibility_intent($functionName, 'public'),
                            'line_count' => $lineCount,
                            'declared_args' => $parameterCounts['declared_args'],
                            'optional_args' => $parameterCounts['optional_args'],
                        ];
                    }
                    break;
                }
                $j++;
            }
        }
    }

    $publicMethodCounts = array_map(
        fn ($classDefinition) => count(array_filter(
            $classDefinition['methods'],
            fn ($methodDefinition) => $methodDefinition['visibility'] === 'public',
        )),
        $classes
    );
    $publicAbstractClassMethodCounts = array_map(
        fn ($classDefinition) => count(array_filter(
            array_merge($classDefinition['abstract_methods'], $classDefinition['concrete_methods']),
            fn ($methodDefinition) => $methodDefinition['visibility'] === 'public',
        )),
        $abstractClasses
    );

    return [
        'imports' => $imports,
        'classes' => $classes,
        'interfaces' => $interfaces,
        'types' => $types,
        'abstract_classes' => $abstractClasses,
        'functions' => $functions,
        'line_count' => line_count_for_content($content),
        'code_line_count' => code_line_count_for_content($content),
        'public_symbol_count' => count($classes) + count($interfaces) + count($abstractClasses) + count($functions) + array_sum($publicMethodCounts) + array_sum($publicAbstractClassMethodCounts),
    ];
}

function extract_batch_from_stdin(): array {
    $payload = stream_get_contents(STDIN);
    $pathsBySourceId = json_decode($payload, true);
    if (!is_array($pathsBySourceId)) {
        fwrite(STDERR, "Expected a JSON object mapping source ids to PHP file paths.\n");
        exit(1);
    }

    $result = [];
    foreach ($pathsBySourceId as $sourceId => $path) {
        if (!is_string($sourceId) || !is_string($path)) {
            fwrite(STDERR, "Expected source ids and paths to be strings.\n");
            exit(1);
        }
        $result[$sourceId] = extract_file($path);
    }
    return $result;
}

if (($argv[1] ?? null) === '--batch') {
    echo json_encode(extract_batch_from_stdin());
} else {
    echo json_encode(extract_file($argv[1]));
}
