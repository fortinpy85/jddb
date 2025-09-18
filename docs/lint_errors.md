# ESLint and TypeScript Errors/Warnings

This document lists the current ESLint and TypeScript errors and warnings identified in the project. These should be addressed to improve code quality and maintainability.

---

## Current Issues

```
C:\JDDB\backend\venv\Lib\site-packages\urllib3\contrib\emscripten\emscripten_fetch_worker.js
0:0 error Parsing error: "parserOptions.project" has been provided for @typescript-eslint/parser.
The file was not found in any of the provided project(s): backend\venv\Lib\site-packages\urllib3\contrib\emscripten\emscripten_fetch_worker.js

C:\JDDB\build.ts
95:5 warning Unexpected console statement no-console
99:3 warning Unexpected console statement no-console
105:5 warning Unexpected console statement no-console
111:38 error 'Bun' is not defined no-undef
115:3 warning Unexpected console statement no-console
142:3 warning Unexpected console statement no-console
145:3 warning Unexpected console statement no-console

C:\JDDB\eslint.config.mjs
0:0 error Parsing error: "parserOptions.project" has been provided for @typescript-eslint/parser.
The file was not found in any of the provided project(s): eslint.config.mjs

C:\JDDB\src\components\BulkUpload.tsx
26:8 warning 'ProgressIndicator' is defined but never used @typescript-eslint/no-unused-vars
26:34 warning 'ProgressStep' is defined but never used @typescript-eslint/no-unused-vars
254:7 warning Unexpected console statement no-console

C:\JDDB\src\components\JobComparison.tsx
28:3 warning 'ArrowRight' is defined but never used @typescript-eslint/no-unused-vars
84:26 warning 'onJobSelect' is defined but never used @typescript-eslint/no-unused-vars
119:7 warning Unexpected console statement no-console
148:7 warning Unexpected console statement no-console
161:9 warning 'getMatchColor' is assigned a value but never used @typescript-eslint/no-unused-vars

C:\JDDB\src\components\JobDetails.tsx
8:15 warning 'JobDescription' is defined but never used @typescript-eslint/no-unused-vars
31:8 warning 'SkeletonLoader' is defined but never used @typescript-eslint/no-unused-vars
62:9 warning Unexpected console statement no-console
106:7 warning Unexpected console statement no-console
439:23 warning Unexpected console statement no-console
440:30 warning 'err' is defined but never used @typescript-eslint/no-unused-vars

C:\JDDB\src\components\JobList.test.tsx
60:7 warning 'mockJobsResponse' is assigned a value but never used @typescript-eslint/no-unused-vars

C:\JDDB\src\components\JobList.tsx
179:9 warning 'StatusIndicator' is assigned a value but never used @typescript-eslint/no-unused-vars

C:\JDDB\src\components\SearchInterface.tsx
66:39 error 'NodeJS' is not defined no-undef
100:7 warning Unexpected console statement no-console
110:7 warning Unexpected console statement no-console

C:\JDDB\src\components\StatsDashboard.tsx
16:3 warning 'AlertCircle' is defined but never used @typescript-eslint/no-unused-vars
52:7 warning Unexpected console statement no-console
65:7 warning Unexpected console statement no-console

C:\JDDB\src\components\ui\breadcrumb.tsx
57:23 warning Unexpected console statement no-console
101:3 warning 'onNavigateHome' is defined but never used @typescript-eslint/no-unused-vars
137:3 warning 'onNavigateHome' is defined but never used @typescript-eslint/no-unused-vars

C:\JDDB\src\components\ui\contextual-menu.tsx
28:3 warning 'FileText' is defined but never used @typescript-eslint/no-unused-vars

C:\JDDB\src\components\ui\empty-state-component.tsx
14:3 warning 'Users' is defined but never used @typescript-eslint/no-unused-vars
18:3 warning 'ArrowRight' is defined but never used @typescript-eslint/no-unused-vars
175:5 warning Unexpected console statement no-console
179:7 warning Unexpected console statement no-console

C:\JDDB\src\components\ui\error-boundary.tsx
66:5 warning Unexpected console statement no-console
243:5 warning Unexpected console statement no-console

C:\JDDB\src\components\ui\error-display.tsx
12:3 warning 'ExternalLink' is defined but never used @typescript-eslint/no-unused-vars

C:\JDDB\src\components\ui\progress-indicator.tsx
4:43 warning 'Upload' is defined but never used @typescript-eslint/no-unused-vars
22:3 warning 'currentStep' is defined but never used @typescript-eslint/no-unused-vars

C:\JDDB\src\components\ui\skeleton-loader.tsx
45:3 warning 'showHeader' is assigned a value but never used @typescript-eslint/no-unused-vars

C:\JDDB\src\components\ui\skeleton.tsx
6:4 error 'React' is not defined no-undef

C:\JDDB\src\components\ui\theme-provider.tsx
35:3 warning 'disableTransitionOnChange' is assigned a value but never used @typescript-eslint/no-unused-vars
36:3 warning 'attribute' is assigned a value but never used @typescript-eslint/no-unused-vars

C:\JDDB\src\components\ui\tooltip.tsx
26:10 warning 'shouldShow' is assigned a value but never used @typescript-eslint/no-unused-vars
27:29 error 'NodeJS' is not defined no-undef

C:\JDDB\src\frontend.tsx
26:5 warning Unexpected console statement no-console

C:\JDDB\src\hooks\useRetry.ts
40:29 error 'NodeJS' is not defined no-undef

C:\JDDB\src\index.tsx
15:19 warning 'req' is defined but never used @typescript-eslint/no-unused-vars
21:19 warning 'req' is defined but never used @typescript-eslint/no-unused-vars
38:3 warning Unexpected console statement no-console

C:\JDDB\src\lib\api.ts
9:3 warning 'SearchResult' is defined but never used @typescript-eslint/no-unused-vars
11:3 warning 'FileMetadata' is defined but never used @typescript-eslint/no-unused-vars
12:3 warning 'StructuredFields' is defined but never used @typescript-eslint/no-unused-vars
13:3 warning 'ProcessingResult' is defined but never used @typescript-eslint/no-unused-vars
14:3 warning 'CircuitBreakerState' is defined but never used @typescript-eslint/no-unused-vars
15:3 warning 'HealthIndicator' is defined but never used @typescript-eslint/no-unused-vars
16:3 warning 'FileProcessingResponse' is defined but never used @typescript-eslint/no-unused-vars
57:12 warning 'error' is defined but never used @typescript-eslint/no-unused-vars
58:5 warning Unexpected console statement no-console
143:7 warning Unexpected console statement no-console
296:11 error Do not assign to the exception parameter no-ex-assign
516:38 warning 'index' is defined but never used @typescript-eslint/no-unused-vars
531:5 warning 'comparison_types' is assigned a value but never used @typescript-eslint/no-unused-vars
532:5 warning 'include_details' is assigned a value but never used @typescript-eslint/no-unused-vars

C:\JDDB\src\lib\store.ts
83:7 warning Unexpected console statement no-console

C:\JDDB\src\test-setup.ts
5:10 warning 'beforeEach' is defined but never used @typescript-eslint/no-unused-vars

C:\JDDB\tailwind.config.js
0:0 error Parsing error: "parserOptions.project" has been provided for @typescript-eslint/parser.
The file was not found in any of the provided project(s): tailwind.config.js

C:\JDDB\tests\accessibility-performance.spec.ts
4:24 warning 'Page' is defined but never used @typescript-eslint/no-unused-vars
6:3 warning 'checkAccessibility' is defined but never used @typescript-eslint/no-unused-vars
7:3 warning 'testResponsiveDesign' is defined but never used @typescript-eslint/no-unused-vars
115:11 warning Unexpected console statement no-console
164:7 warning Unexpected console statement no-console
174:7 warning Unexpected console statement no-console
288:5 warning Unexpected console statement no-console
322:5 warning Unexpected console statement no-console
348:5 warning Unexpected console statement no-console
362:5 warning Unexpected console statement no-console

C:\JDDB\tests\dashboard.spec.ts
2:10 warning 'mockApiResponse' is defined but never used @typescript-eslint/no-unused-vars
2:27 warning 'waitForApiCall' is defined but never used @typescript-eslint/no-unused-vars

C:\JDDB\tests\gui-enhancements.spec.ts
132:17 warning 'loadingIndicators' is assigned a value but never used @typescript-eslint/no-unused-vars
289:17 warning 'hasHoverClass' is assigned a value but never used @typescript-eslint/no-unused-vars
368:13 warning 'errorElements' is assigned a value but never used @typescript-eslint/no-unused-vars

C:\JDDB\tests\search.spec.ts
356:16 warning 'error' is defined but never used @typescript-eslint/no-unused-vars
358:9 warning Unexpected console statement no-console

C:\JDDB\tests\upload.spec.ts
2:8 warning 'path' is defined but never used @typescript-eslint/no-unused-vars

C:\JDDB\tests\utils\test-helpers.ts
184:7 warning Unexpected console statement no-console
198:9 warning Unexpected console statement no-console

```