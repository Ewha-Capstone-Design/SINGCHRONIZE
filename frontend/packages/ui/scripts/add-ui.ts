import { execa } from 'execa';

const components = process.argv.slice(2);

if (components.length === 0) {
  console.error('❌ 컴포넌트 이름을 전달하세요. ex) pnpm ui:add button');
  process.exit(1);
}

// shadcn 실행
await execa('pnpm', ['dlx', 'shadcn@latest', 'add', ...components], { stdio: 'inherit' });

// codemod 실행
await execa('tsx', ['scripts/shadcn-transform.ts'], { stdio: 'inherit' });
