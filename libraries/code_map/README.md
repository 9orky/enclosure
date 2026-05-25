# code-map

`code-map` extracts source-code dependencies and builds dependency graphs.

```python
from pathlib import Path

from code_map import build_dependency_graph


```

Graph nodes use canonical extensionless source IDs, so equivalent Python,
TypeScript, and PHP projects can be compared through the same graph shape.
