import fs from 'fs';
import path from 'path';

const ROOT = path.resolve(process.cwd(), 'src');

function toPascalCase(name: string) {
  return name
    .trim()
    .split(/[^a-zA-Z0-9]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join('');
}

function walk(dir: string) {
  if (!fs.existsSync(dir)) return;

  for (const entry of fs.readdirSync(dir)) {
    const full = path.join(dir, entry);
    if (fs.statSync(full).isDirectory()) {
      walk(full);
    } else if (full.endsWith('.tsx')) {
      fixFile(full);
    }
  }
}

function fixFile(filePath: string) {
  const fileName = path.basename(filePath); // input.tsx
  const base = fileName.replace('.tsx', ''); // input
  const componentName = toPascalCase(base); // Input

  const targetDir = path.join(ROOT, 'components', base);
  const targetFile = path.join(targetDir, `${componentName}.tsx`);
  const componentsIndex = path.join(ROOT, 'components', 'index.ts');

  let code = fs.readFileSync(filePath, 'utf8');

  // 1️. utils alias → 상대경로
  if (code.includes(`"src/lib/utils"`)) {
    const fromDir = targetDir;
    const utilsPath = path.join(ROOT, 'lib/utils');
    let relative = path.relative(fromDir, utilsPath);

    if (!relative.startsWith('.')) relative = './' + relative;
    relative = relative.replace(/\\/g, '/');

    code = code.replace(/"src\/lib\/utils"/g, `"${relative}"`);
  }

  // 2️. export function / const → default export
  code = code.replace(new RegExp(`export \\{\\s*${componentName}\\s*\\};?`, 'g'), '');

  code = code.replace(
    new RegExp(`export function ${componentName}`),
    `function ${componentName}`
  );
  code = code.replace(
    new RegExp(`export const ${componentName}`),
    `const ${componentName}`
  );

  if (!code.includes(`export default ${componentName}`)) {
    code += `\n\nexport default ${componentName};\n`;
  }

  // 3️. 파일 생성
  fs.mkdirSync(targetDir, { recursive: true });
  fs.writeFileSync(targetFile, code);

  // 4️. components/index.ts 업데이트 자동화
  const exportLine = `export { default as ${componentName} } from "./${base}/${componentName}";\n`;

  let indexCode = '';
  if (fs.existsSync(componentsIndex)) {
    indexCode = fs.readFileSync(componentsIndex, 'utf8');
    if (indexCode.includes(exportLine)) return;
  }

  fs.writeFileSync(componentsIndex, indexCode + exportLine);
}

walk(path.join(ROOT, 'components/ui'));
