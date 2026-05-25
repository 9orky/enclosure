#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

function buildLineStarts(content) {
    const lineStarts = [0];
    for (let index = 0; index < content.length; index += 1) {
        if (content[index] === '\n') {
            lineStarts.push(index + 1);
        }
    }
    return lineStarts;
}

function lineNumberAt(lineStarts, index) {
    let low = 0;
    let high = lineStarts.length - 1;
    while (low <= high) {
        const middle = Math.floor((low + high) / 2);
        if (lineStarts[middle] <= index) {
            low = middle + 1;
        } else {
            high = middle - 1;
        }
    }
    return high + 1;
}

function lineSpan(lineStarts, startIndex, endIndex) {
    return lineNumberAt(lineStarts, endIndex) - lineNumberAt(lineStarts, startIndex) + 1;
}

function findMatchingBrace(content, openBraceIndex) {
    let depth = 0;
    let inSingleQuote = false;
    let inDoubleQuote = false;
    let inTemplate = false;
    let inLineComment = false;
    let inBlockComment = false;

    for (let index = openBraceIndex; index < content.length; index += 1) {
        const current = content[index];
        const next = content[index + 1];

        if (inLineComment) {
            if (current === '\n') {
                inLineComment = false;
            }
            continue;
        }
        if (inBlockComment) {
            if (current === '*' && next === '/') {
                inBlockComment = false;
                index += 1;
            }
            continue;
        }
        if (inSingleQuote) {
            if (current === '\\') {
                index += 1;
                continue;
            }
            if (current === '\'') {
                inSingleQuote = false;
            }
            continue;
        }
        if (inDoubleQuote) {
            if (current === '\\') {
                index += 1;
                continue;
            }
            if (current === '"') {
                inDoubleQuote = false;
            }
            continue;
        }
        if (inTemplate) {
            if (current === '\\') {
                index += 1;
                continue;
            }
            if (current === '`') {
                inTemplate = false;
            }
            continue;
        }

        if (current === '/' && next === '/') {
            inLineComment = true;
            index += 1;
            continue;
        }
        if (current === '/' && next === '*') {
            inBlockComment = true;
            index += 1;
            continue;
        }
        if (current === '\'') {
            inSingleQuote = true;
            continue;
        }
        if (current === '"') {
            inDoubleQuote = true;
            continue;
        }
        if (current === '`') {
            inTemplate = true;
            continue;
        }
        if (current === '{') {
            depth += 1;
            continue;
        }
        if (current === '}') {
            depth -= 1;
            if (depth === 0) {
                return index;
            }
        }
    }
    return openBraceIndex;
}

function findMatchingParen(content, openParenIndex) {
    let depth = 0;
    let inSingleQuote = false;
    let inDoubleQuote = false;
    let inTemplate = false;
    let inLineComment = false;
    let inBlockComment = false;

    for (let index = openParenIndex; index < content.length; index += 1) {
        const current = content[index];
        const next = content[index + 1];

        if (inLineComment) {
            if (current === '\n') {
                inLineComment = false;
            }
            continue;
        }
        if (inBlockComment) {
            if (current === '*' && next === '/') {
                inBlockComment = false;
                index += 1;
            }
            continue;
        }
        if (inSingleQuote) {
            if (current === '\\') {
                index += 1;
                continue;
            }
            if (current === '\'') {
                inSingleQuote = false;
            }
            continue;
        }
        if (inDoubleQuote) {
            if (current === '\\') {
                index += 1;
                continue;
            }
            if (current === '"') {
                inDoubleQuote = false;
            }
            continue;
        }
        if (inTemplate) {
            if (current === '\\') {
                index += 1;
                continue;
            }
            if (current === '`') {
                inTemplate = false;
            }
            continue;
        }

        if (current === '/' && next === '/') {
            inLineComment = true;
            index += 1;
            continue;
        }
        if (current === '/' && next === '*') {
            inBlockComment = true;
            index += 1;
            continue;
        }
        if (current === '\'') {
            inSingleQuote = true;
            continue;
        }
        if (current === '"') {
            inDoubleQuote = true;
            continue;
        }
        if (current === '`') {
            inTemplate = true;
            continue;
        }
        if (current === '(') {
            depth += 1;
            continue;
        }
        if (current === ')') {
            depth -= 1;
            if (depth === 0) {
                return index;
            }
        }
    }
    return openParenIndex;
}

function splitTopLevelParameters(parameterText) {
    const parameters = [];
    let startIndex = 0;
    let depth = 0;
    let inSingleQuote = false;
    let inDoubleQuote = false;
    let inTemplate = false;

    for (let index = 0; index < parameterText.length; index += 1) {
        const current = parameterText[index];

        if (inSingleQuote) {
            if (current === '\\') {
                index += 1;
                continue;
            }
            if (current === '\'') {
                inSingleQuote = false;
            }
            continue;
        }
        if (inDoubleQuote) {
            if (current === '\\') {
                index += 1;
                continue;
            }
            if (current === '"') {
                inDoubleQuote = false;
            }
            continue;
        }
        if (inTemplate) {
            if (current === '\\') {
                index += 1;
                continue;
            }
            if (current === '`') {
                inTemplate = false;
            }
            continue;
        }

        if (current === '\'') {
            inSingleQuote = true;
            continue;
        }
        if (current === '"') {
            inDoubleQuote = true;
            continue;
        }
        if (current === '`') {
            inTemplate = true;
            continue;
        }
        if ('({[<'.includes(current)) {
            depth += 1;
            continue;
        }
        if (')}]>'.includes(current)) {
            depth = Math.max(0, depth - 1);
            continue;
        }
        if (current === ',' && depth === 0) {
            parameters.push(parameterText.slice(startIndex, index).trim());
            startIndex = index + 1;
        }
    }

    parameters.push(parameterText.slice(startIndex).trim());
    return parameters.filter(Boolean);
}

function hasTopLevelCharacter(value, character) {
    let depth = 0;
    for (let index = 0; index < value.length; index += 1) {
        const current = value[index];
        if ('({[<'.includes(current)) {
            depth += 1;
            continue;
        }
        if (')}]>'.includes(current)) {
            depth = Math.max(0, depth - 1);
            continue;
        }
        if (current === character && depth === 0) {
            return true;
        }
    }
    return false;
}

function parameterCounts(parameterText) {
    const parameters = splitTopLevelParameters(parameterText);
    return {
        declared_args: parameters.length,
        optional_args: parameters.filter(parameter => {
            const withoutModifiers = parameter
                .replace(/^(?:(?:public|protected|private|readonly|override|static)\s+)*/g, '')
                .trim();
            return withoutModifiers.startsWith('...')
                || hasTopLevelCharacter(withoutModifiers, '=')
                || /^[A-Za-z_$][\w$]*\?(\s*[:=]|$)/.test(withoutModifiers);
        }).length,
    };
}

function parameterCountsFromParen(content, openParenIndex) {
    const closeParenIndex = findMatchingParen(content, openParenIndex);
    return parameterCounts(content.slice(openParenIndex + 1, closeParenIndex));
}

function parameterPropertiesFromParen(content, openParenIndex) {
    const closeParenIndex = findMatchingParen(content, openParenIndex);
    return splitTopLevelParameters(content.slice(openParenIndex + 1, closeParenIndex))
        .map(parameter => parameterProperty(parameter))
        .filter(property => property !== null);
}

function parameterProperty(parameter) {
    const withoutDecorators = parameter.replace(/^@\w+(?:\([^)]*\))?\s*/g, '').trim();
    const match = withoutDecorators.match(/^(?:(?:public|protected|private|readonly|override)\s+)+(?:\.\.\.\s*)?([A-Za-z_$][\w$]*)(\?)?/);
    if (match === null) {
        return null;
    }
    return {
        name: match[1],
        is_optional: Boolean(match[2]) || propertyTextIsOptional(withoutDecorators),
    };
}

function propertyTextIsOptional(value) {
    const typeMatch = value.match(/:\s*([^=;]+)/);
    const initializerMatch = value.match(/=\s*([^;]+)/);
    return Boolean(typeMatch && /\b(null|undefined)\b/.test(typeMatch[1]))
        || Boolean(initializerMatch && /^(null|undefined)\b/.test(initializerMatch[1].trim()));
}

function addProperty(properties, name, isOptional) {
    const existing = properties.get(name);
    properties.set(name, Boolean(existing) || isOptional);
}

function collectSignaturesFromText(value, lineStarts, baseIndex) {
    const signatures = [];

    function addSignature(kind, matchIndex, matchText, parameterText) {
        const counts = kind === 'index'
            ? { declared_args: 1, optional_args: 0 }
            : parameterCounts(parameterText);
        signatures.push({
            kind,
            line_count: lineSpan(
                lineStarts,
                baseIndex + matchIndex,
                baseIndex + matchIndex + matchText.length,
            ),
            declared_args: counts.declared_args,
            optional_args: counts.optional_args,
        });
    }

    let match;
    const constructRegex = /(?:^|\n|;)\s*new\s*\(([^)]*)\)\s*:/g;
    while ((match = constructRegex.exec(value)) !== null) {
        addSignature('construct', match.index, match[0], match[1]);
    }

    const callRegex = /(?:^|\n|;)\s*\(([^)]*)\)\s*:/g;
    while ((match = callRegex.exec(value)) !== null) {
        addSignature('call', match.index, match[0], match[1]);
    }

    const indexRegex = /(?:^|\n|;)\s*\[[^\]]+\]\s*:/g;
    while ((match = indexRegex.exec(value)) !== null) {
        addSignature('index', match.index, match[0], '');
    }

    return signatures;
}

function isWithinRanges(index, ranges) {
    return ranges.some(range => index >= range.start && index <= range.end);
}

function codeLineCount(content) {
    return content
        .split('\n')
        .filter(line => {
            const trimmed = line.trim();
            return trimmed && !trimmed.startsWith('//') && !trimmed.startsWith('/*') && !trimmed.startsWith('*');
        })
        .length;
}

function withoutExtension(value) {
    return value.replace(/\.[cm]?[jt]sx?$/, '');
}

function normalizedImportPath(importPath, isRelative, filePath, sourcesRoot) {
    if (!isRelative) {
        return importPath.replace(/^\/+|\/+$/g, '');
    }

    const absolutePath = path.resolve(path.dirname(filePath), importPath);
    return withoutExtension(path.relative(sourcesRoot, absolutePath).split(path.sep).join('/'));
}

function collectImports(content, filePath, sourcesRoot) {
    const imports = [];
    let statementId = 0;

    function addImport(
        importPath,
        crossingType = 'module',
        isAliased = false,
        joinable = false,
    ) {
        const isRelative = importPath.startsWith('.');
        const normalizedPath = normalizedImportPath(
            importPath,
            isRelative,
            filePath,
            sourcesRoot,
        );
        statementId += 1;
        imports.push({
            path: importPath,
            is_relative: isRelative,
            normalized_path: normalizedPath,
            imported_name: '',
            is_aliased: isAliased,
            crossing_type: crossingType,
            file_barrier_crossed: true,
            statement_id: statementId,
            join_key: joinable ? normalizedPath : '',
            uses_joined_import: joinable,
        });
    }

    function hasAliasedImport(importSpecifiers) {
        const specifiers = importSpecifiers.trim().replace(/^type\s+/, '');
        if (!specifiers) {
            return false;
        }
        if (/\*\s+as\s+[$\w]+/.test(specifiers)) {
            return true;
        }

        const namedImport = specifiers.match(/\{([\s\S]*?)\}/);
        return namedImport !== null && /\bas\b/.test(namedImport[1]);
    }

    let match;
    const importRegex = /import\s+([\s\S]*?)\s+from\s+['"](.*?)['"]/g;
    while ((match = importRegex.exec(content)) !== null) {
        const importSpecifiers = match[1].trim().replace(/^type\s+/, '');
        const isNamespaceImport = importSpecifiers.startsWith('*');
        addImport(
            match[2],
            Boolean(importSpecifiers) && !isNamespaceImport
                ? 'symbol'
                : 'module',
            hasAliasedImport(importSpecifiers),
            !isNamespaceImport,
        );
    }

    const sideEffectImportRegex = /import\s+['"](.*?)['"]/g;
    while ((match = sideEffectImportRegex.exec(content)) !== null) {
        addImport(match[1]);
    }

    const dynamicImportRegex = /import\(['"](.*?)['"]\)/g;
    while ((match = dynamicImportRegex.exec(content)) !== null) {
        addImport(match[1]);
    }

    const requireRegex = /require\(['"](.*?)['"]\)/g;
    while ((match = requireRegex.exec(content)) !== null) {
        addImport(match[1]);
    }

    return imports;
}

function collectClasses(content, lineStarts) {
    const classes = [];
    const classRanges = [];
    const classRegex = /\b(export\s+(?:default\s+)?)?class\s+([A-Za-z_$][\w$]*)[^{]*\{/g;
    let match;

    while ((match = classRegex.exec(content)) !== null) {
        if (/\babstract\s+$/.test(content.slice(Math.max(0, match.index - 32), match.index))) {
            continue;
        }
        const openBraceIndex = content.indexOf('{', match.index);
        const closeBraceIndex = findMatchingBrace(content, openBraceIndex);
        const body = content.slice(openBraceIndex + 1, closeBraceIndex);
        const methods = [];
        const methodRanges = [];
        const properties = new Map();
        const seenMethods = new Set();
        const methodRegex = /(?:^|\n)\s*((?:public|protected|private|static|async|get|set|readonly|override)\s+)*([#A-Za-z_$][\w$]*)\s*\(/g;
        let methodMatch;

        while ((methodMatch = methodRegex.exec(body)) !== null) {
            const methodName = methodMatch[2];
            if (seenMethods.has(methodName)) {
                continue;
            }
            seenMethods.add(methodName);
            const methodStart = openBraceIndex + 1 + methodMatch.index;
            const methodOpenParen = body.indexOf('(', methodMatch.index);
            const methodCloseParen = findMatchingParen(body, methodOpenParen);
            const methodOpenBrace = body.indexOf('{', methodCloseParen);
            if (methodOpenBrace === -1) {
                continue;
            }
            const methodBraceIndex = openBraceIndex + 1 + methodOpenBrace;
            const methodCloseBraceIndex = findMatchingBrace(content, methodBraceIndex);
            methodRanges.push({
                start: methodMatch.index,
                end: methodCloseBraceIndex - openBraceIndex - 1,
            });
            const counts = parameterCountsFromParen(
                body,
                methodOpenParen,
            );
            const methodVisibility = methodVisibilityFromTokens(
                methodMatch[1] || '',
                methodName,
            );
            methods.push({
                name: methodName,
                visibility: methodVisibility,
                visibility_intent: visibilityIntent(methodName, methodVisibility),
                line_count: lineSpan(lineStarts, methodStart, methodCloseBraceIndex),
                declared_args: counts.declared_args,
                optional_args: counts.optional_args,
            });
            if (methodName === 'constructor') {
                for (const property of parameterPropertiesFromParen(body, methodOpenParen)) {
                    addProperty(properties, property.name, property.is_optional);
                }
            }
        }

        const propertyRegex = /(?:^|\n)\s*(?:(?:public|protected|private|static|readonly|declare|override|abstract|accessor)\s+)*([#A-Za-z_$][\w$]*)(\?)?\s*(?:(?::([^;=\n{]+))|(?:=\s*([^;\n]+))|;)/g;
        let propertyMatch;
        while ((propertyMatch = propertyRegex.exec(body)) !== null) {
            if (isWithinRanges(propertyMatch.index, methodRanges)) {
                continue;
            }
            addProperty(
                properties,
                propertyMatch[1],
                Boolean(propertyMatch[2]) || propertyTextIsOptional(propertyMatch[0]),
            );
        }
        classes.push({
            name: match[2],
            visibility: match[1] ? 'public' : 'private',
            visibility_intent: visibilityIntent(match[2], match[1] ? 'public' : 'private'),
            methods,
            properties: Array.from(properties, ([name, is_optional]) => ({
                name,
                is_optional,
            })),
            line_count: lineSpan(lineStarts, match.index, closeBraceIndex),
        });
        classRanges.push({ start: match.index, end: closeBraceIndex });
    }

    return { classes, classRanges };
}

function collectInterfaces(content, lineStarts) {
    const interfaces = [];
    const interfaceRegex = /\b(export\s+)?interface\s+([A-Za-z_$][\w$]*)([^{]*)\{/g;
    let match;

    while ((match = interfaceRegex.exec(content)) !== null) {
        const openBraceIndex = content.indexOf('{', match.index);
        const closeBraceIndex = findMatchingBrace(content, openBraceIndex);
        const body = content.slice(openBraceIndex + 1, closeBraceIndex);
        const methods = [];
        const properties = new Map();
        const signatures = collectSignaturesFromText(
            body,
            lineStarts,
            openBraceIndex + 1,
        );

        const methodRegex = /(?:^|\n)\s*([A-Za-z_$][\w$]*)\??\s*\(([^)]*)\)/g;
        let methodMatch;
        while ((methodMatch = methodRegex.exec(body)) !== null) {
            const methodName = methodMatch[1];
            if (methodName === 'new') {
                continue;
            }
            const openParenIndex = body.indexOf('(', methodMatch.index);
            const closeParenIndex = findMatchingParen(body, openParenIndex);
            const counts = parameterCountsFromParen(body, openParenIndex);
            methods.push({
                name: methodName,
                visibility: 'public',
                visibility_intent: visibilityIntent(methodName, 'public'),
                line_count: lineSpan(
                    lineStarts,
                    openBraceIndex + 1 + methodMatch.index,
                    openBraceIndex + 1 + closeParenIndex,
                ),
                declared_args: counts.declared_args,
                optional_args: counts.optional_args,
            });
        }

        const propertyRegex = /(?:^|\n)\s*(?:(?:readonly)\s+)*([A-Za-z_$][\w$]*)(\?)?\s*:\s*([^;\n]+)/g;
        let propertyMatch;
        while ((propertyMatch = propertyRegex.exec(body)) !== null) {
            const propertyName = propertyMatch[1];
            addProperty(
                properties,
                propertyName,
                Boolean(propertyMatch[2]) || propertyTextIsOptional(propertyMatch[0]),
            );
        }

        interfaces.push({
            name: match[2],
            visibility: match[1] ? 'public' : 'private',
            visibility_intent: visibilityIntent(match[2], match[1] ? 'public' : 'private'),
            methods,
            properties: Array.from(properties, ([name, is_optional]) => ({
                name,
                is_optional,
            })),
            signatures,
            line_count: lineSpan(lineStarts, match.index, closeBraceIndex),
        });
    }

    return interfaces;
}

function findTopLevelSemicolon(content, startIndex) {
    let depth = 0;
    let inSingleQuote = false;
    let inDoubleQuote = false;
    let inTemplate = false;
    let inLineComment = false;
    let inBlockComment = false;

    for (let index = startIndex; index < content.length; index += 1) {
        const current = content[index];
        const next = content[index + 1];

        if (inLineComment) {
            if (current === '\n') {
                inLineComment = false;
            }
            continue;
        }
        if (inBlockComment) {
            if (current === '*' && next === '/') {
                inBlockComment = false;
                index += 1;
            }
            continue;
        }
        if (inSingleQuote) {
            if (current === '\\') {
                index += 1;
                continue;
            }
            if (current === '\'') {
                inSingleQuote = false;
            }
            continue;
        }
        if (inDoubleQuote) {
            if (current === '\\') {
                index += 1;
                continue;
            }
            if (current === '"') {
                inDoubleQuote = false;
            }
            continue;
        }
        if (inTemplate) {
            if (current === '\\') {
                index += 1;
                continue;
            }
            if (current === '`') {
                inTemplate = false;
            }
            continue;
        }

        if (current === '/' && next === '/') {
            inLineComment = true;
            index += 1;
            continue;
        }
        if (current === '/' && next === '*') {
            inBlockComment = true;
            index += 1;
            continue;
        }
        if (current === '\'') {
            inSingleQuote = true;
            continue;
        }
        if (current === '"') {
            inDoubleQuote = true;
            continue;
        }
        if (current === '`') {
            inTemplate = true;
            continue;
        }
        if ('({[<'.includes(current)) {
            depth += 1;
            continue;
        }
        if (')}]>'.includes(current)) {
            depth = Math.max(0, depth - 1);
            continue;
        }
        if (current === ';' && depth === 0) {
            return index;
        }
    }
    return content.length - 1;
}

function collectTypes(content, lineStarts) {
    const types = [];
    const typeRegex = /\b(export\s+)?type\s+([A-Za-z_$][\w$]*)\s*=/g;
    let match;

    while ((match = typeRegex.exec(content)) !== null) {
        const valueStartIndex = typeRegex.lastIndex;
        const endIndex = findTopLevelSemicolon(content, valueStartIndex);
        const value = content.slice(valueStartIndex, endIndex);
        const properties = new Map();
        const signatures = collectSignaturesFromText(value, lineStarts, valueStartIndex);
        const openBraceIndex = value.indexOf('{');

        if (openBraceIndex !== -1) {
            const closeBraceIndex = findMatchingBrace(value, openBraceIndex);
            const body = value.slice(openBraceIndex + 1, closeBraceIndex);
            const propertyRegex = /(?:^|\n|;)\s*(?:(?:readonly)\s+)*([A-Za-z_$][\w$]*)(\?)?\s*:\s*([^;\n]+)/g;
            let propertyMatch;
            while ((propertyMatch = propertyRegex.exec(body)) !== null) {
                const propertyName = propertyMatch[1];
                addProperty(
                    properties,
                    propertyName,
                    Boolean(propertyMatch[2]) || propertyTextIsOptional(propertyMatch[0]),
                );
            }
        }

        types.push({
            name: match[2],
            visibility: match[1] ? 'public' : 'private',
            visibility_intent: visibilityIntent(match[2], match[1] ? 'public' : 'private'),
            properties: Array.from(properties, ([name, is_optional]) => ({
                name,
                is_optional,
            })),
            signatures,
            line_count: lineSpan(lineStarts, match.index, endIndex),
        });
    }

    return types;
}

function collectAbstractClasses(content, lineStarts) {
    const abstractClasses = [];
    const classRegex = /\b(export\s+(?:default\s+)?)?abstract\s+class\s+([A-Za-z_$][\w$]*)[^{]*\{/g;
    let match;

    while ((match = classRegex.exec(content)) !== null) {
        const openBraceIndex = content.indexOf('{', match.index);
        const closeBraceIndex = findMatchingBrace(content, openBraceIndex);
        const body = content.slice(openBraceIndex + 1, closeBraceIndex);
        const abstractMethods = [];
        const concreteMethods = [];
        const methodRanges = [];
        const properties = new Map();
        const seenMethods = new Set();
        const methodRegex = /(?:^|\n)\s*((?:public|protected|private|static|async|get|set|readonly|override|abstract)\s+)*([#A-Za-z_$][\w$]*)\s*\(/g;
        let methodMatch;

        while ((methodMatch = methodRegex.exec(body)) !== null) {
            const methodName = methodMatch[2];
            if (seenMethods.has(methodName)) {
                continue;
            }
            seenMethods.add(methodName);
            const methodStart = openBraceIndex + 1 + methodMatch.index;
            const methodOpenParen = body.indexOf('(', methodMatch.index);
            const methodCloseParen = findMatchingParen(body, methodOpenParen);
            const methodOpenBrace = body.indexOf('{', methodCloseParen);
            const methodSemicolon = body.indexOf(';', methodCloseParen);
            const isAbstract = /\babstract\b/.test(methodMatch[1] || '')
                || methodOpenBrace === -1
                || (methodSemicolon !== -1 && methodSemicolon < methodOpenBrace);
            const methodEnd = isAbstract
                ? (methodSemicolon === -1 ? methodCloseParen : methodSemicolon)
                : findMatchingBrace(content, openBraceIndex + 1 + methodOpenBrace);
            methodRanges.push({
                start: methodMatch.index,
                end: methodEnd - openBraceIndex - 1,
            });
            const counts = parameterCountsFromParen(body, methodOpenParen);
            const methodVisibility = methodVisibilityFromTokens(
                methodMatch[1] || '',
                methodName,
            );
            const method = {
                name: methodName,
                visibility: methodVisibility,
                visibility_intent: visibilityIntent(methodName, methodVisibility),
                line_count: lineSpan(lineStarts, methodStart, methodEnd),
                declared_args: counts.declared_args,
                optional_args: counts.optional_args,
            };
            if (isAbstract) {
                abstractMethods.push(method);
            } else {
                concreteMethods.push(method);
            }
            if (methodName === 'constructor') {
                for (const property of parameterPropertiesFromParen(body, methodOpenParen)) {
                    addProperty(properties, property.name, property.is_optional);
                }
            }
        }

        const propertyRegex = /(?:^|\n)\s*(?:(?:public|protected|private|static|readonly|declare|override|abstract|accessor)\s+)*([#A-Za-z_$][\w$]*)(\?)?\s*(?:(?::([^;=\n{]+))|(?:=\s*([^;\n]+))|;)/g;
        let propertyMatch;
        while ((propertyMatch = propertyRegex.exec(body)) !== null) {
            if (isWithinRanges(propertyMatch.index, methodRanges)) {
                continue;
            }
            addProperty(
                properties,
                propertyMatch[1],
                Boolean(propertyMatch[2]) || propertyTextIsOptional(propertyMatch[0]),
            );
        }
        abstractClasses.push({
            name: match[2],
            visibility: match[1] ? 'public' : 'private',
            visibility_intent: visibilityIntent(match[2], match[1] ? 'public' : 'private'),
            abstract_methods: abstractMethods,
            concrete_methods: concreteMethods,
            properties: Array.from(properties, ([name, is_optional]) => ({
                name,
                is_optional,
            })),
            line_count: lineSpan(lineStarts, match.index, closeBraceIndex),
        });
    }

    return abstractClasses;
}

function collectFunctions(content, lineStarts, classRanges) {
    const functions = [];
    const seenNames = new Set();

    function addFunction(name, startIndex, endIndex, counts, visibility) {
        if (!name || seenNames.has(name) || isWithinRanges(startIndex, classRanges)) {
            return;
        }
        seenNames.add(name);
        functions.push({
            name,
            visibility,
            visibility_intent: visibilityIntent(name, visibility),
            line_count: lineSpan(lineStarts, startIndex, endIndex),
            declared_args: counts.declared_args,
            optional_args: counts.optional_args,
        });
    }

    let match;
    const functionRegex = /\b(export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(/g;
    while ((match = functionRegex.exec(content)) !== null) {
        const openParenIndex = content.indexOf('(', match.index);
        const closeParenIndex = findMatchingParen(content, openParenIndex);
        const openBraceIndex = content.indexOf('{', closeParenIndex);
        if (openBraceIndex === -1) {
            continue;
        }
        addFunction(
            match[2],
            match.index,
            findMatchingBrace(content, openBraceIndex),
            parameterCountsFromParen(content, openParenIndex),
            match[1] ? 'public' : 'private',
        );
    }

    const arrowFunctionRegex = /\b(export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>\s*(\{)?/g;
    while ((match = arrowFunctionRegex.exec(content)) !== null) {
        const hasBlockBody = match[4] === '{';
        const openBraceIndex = hasBlockBody ? content.indexOf('{', match.index) : match.index;
        const endIndex = hasBlockBody ? findMatchingBrace(content, openBraceIndex) : match.index;
        addFunction(
            match[2],
            match.index,
            endIndex,
            parameterCounts(match[3].replace(/^\(|\)$/g, '')),
            match[1] ? 'public' : 'private',
        );
    }

    return functions;
}

function methodVisibilityFromTokens(tokens, name) {
    if (name.startsWith('#')) {
        return 'private';
    }
    if (/\bprivate\b/.test(tokens)) {
        return 'private';
    }
    if (/\bprotected\b/.test(tokens)) {
        return 'protected';
    }
    return 'public';
}

function visibilityIntent(name, visibility) {
    if (name.startsWith('#') || (name.startsWith('__') && !name.endsWith('__'))) {
        return 'private';
    }
    if (name.startsWith('_') && !name.endsWith('__')) {
        return 'protected';
    }
    return visibility;
}

function extractFile(filePath, sourcesRoot) {
    const content = fs.readFileSync(filePath, 'utf8');
    const lineStarts = buildLineStarts(content);
    const { classes, classRanges } = collectClasses(content, lineStarts);
    const interfaces = collectInterfaces(content, lineStarts);
    const types = collectTypes(content, lineStarts);
    const abstractClasses = collectAbstractClasses(content, lineStarts);
    const functions = collectFunctions(content, lineStarts, classRanges);

    return {
        imports: collectImports(content, filePath, sourcesRoot),
        classes,
        interfaces,
        types,
        abstract_classes: abstractClasses,
        functions,
        line_count: content.split('\n').length,
        code_line_count: codeLineCount(content),
        public_symbol_count: publicSymbolCount(content),
    };
}

function publicSymbolCount(content) {
    const symbols = new Set();
    let match;

    const classRegex = /\bexport\s+(?:default\s+)?class\s+([A-Za-z_$][\w$]*)/g;
    while ((match = classRegex.exec(content)) !== null) {
        symbols.add(match[1]);
    }

    const abstractClassRegex = /\bexport\s+(?:default\s+)?abstract\s+class\s+([A-Za-z_$][\w$]*)/g;
    while ((match = abstractClassRegex.exec(content)) !== null) {
        symbols.add(match[1]);
    }

    const interfaceRegex = /\bexport\s+interface\s+([A-Za-z_$][\w$]*)/g;
    while ((match = interfaceRegex.exec(content)) !== null) {
        symbols.add(match[1]);
    }

    const typeRegex = /\bexport\s+type\s+([A-Za-z_$][\w$]*)/g;
    while ((match = typeRegex.exec(content)) !== null) {
        symbols.add(match[1]);
    }

    const functionRegex = /\bexport\s+(?:async\s+)?function\s+([A-Za-z_$][\w$]*)/g;
    while ((match = functionRegex.exec(content)) !== null) {
        symbols.add(match[1]);
    }

    const arrowFunctionRegex = /\bexport\s+(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=/g;
    while ((match = arrowFunctionRegex.exec(content)) !== null) {
        symbols.add(match[1]);
    }

    return symbols.size;
}

console.log(JSON.stringify(extractFile(
    path.resolve(process.argv[2]),
    process.argv[3] ? path.resolve(process.argv[3]) : process.cwd(),
)));
