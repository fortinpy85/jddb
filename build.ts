#!/usr/bin/env bun
import { build, type BuildConfig } from "bun";
import plugin from "bun-plugin-tailwind";
import { existsSync } from "fs";
import { rm } from "fs/promises";
import path from "path";

const HELP_TEXT = `
🏗️  Bun Build Script

Usage: bun run build.ts [options]

Common Options:
  --outdir <path>          Output directory (default: "dist")
  --minify                 Enable minification (or --minify.whitespace, --minify.syntax, etc)
  --source-map <type>      Sourcemap type: none|linked|inline|external
  --target <target>        Build target: browser|bun|node
  --format <format>        Output format: esm|cjs|iife
  --splitting              Enable code splitting
  --packages <type>        Package handling: bundle|external
  --public-path <path>     Public path for assets
  --env <mode>             Environment handling: inline|disable|prefix*
  --conditions <list>      Package.json export conditions (comma separated)
  --external <list>        External packages (comma separated)
  --banner <text>          Add banner text to output
  --footer <text>          Add footer text to output
  --define <obj>           Define global constants (e.g. --define.VERSION=1.0.0)
  --help, -h               Show this help message

Example:
  bun run build.ts --outdir=dist --minify --source-map=linked --external=react,react-dom
`;

function toCamelCase(str: string): string {
  return str.replace(/-([a-z])/g, (g) => g[1].toUpperCase());
}

function parseValue(value: string): any {
  if (value === "true") return true;
  if (value === "false") return false;
  if (!isNaN(Number(value))) return Number(value);
  if (value.includes(",")) return value.split(",").map((v) => v.trim());
  return value;
}

function parseArgs(): Partial<BuildConfig> {
  const config: Record<string, any> = {};
  const args = process.argv.slice(2);

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (!arg.startsWith("--")) continue;

    if (arg.startsWith("--no-")) {
      const key = toCamelCase(arg.slice(5));
      config[key] = false;
      continue;
    }

    let key: string;
    let value: any = true;

    if (arg.includes("=")) {
      [key, value] = arg.slice(2).split("=", 2);
      value = parseValue(value);
    } else if (i + 1 < args.length && !args[i + 1].startsWith("--")) {
      key = arg.slice(2);
      value = parseValue(args[++i]);
    } else {
      key = arg.slice(2);
    }

    key = toCamelCase(key);

    if (key.includes(".")) {
      const [parentKey, childKey] = key.split(".");
      config[parentKey] = config[parentKey] || {};
      config[parentKey][childKey] = value;
    } else {
      config[key] = value;
    }
  }

  return config as Partial<BuildConfig>;
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${["B", "KB", "MB", "GB"][i]}`;
}

async function main() {
  if (process.argv.includes("--help") || process.argv.includes("-h")) {
    console.error(HELP_TEXT);
    process.exit(0);
  }

  console.log("\n🚀 Starting build process...\n");

  const cliConfig = parseArgs();
  const outdir = cliConfig.outdir || path.join(process.cwd(), "dist");

  if (existsSync(outdir)) {
    console.log(`🗑️ Cleaning previous build at ${outdir}`);
    await rm(outdir, { recursive: true, force: true });
  }

  const start = performance.now();

  const entrypoints = Array.from(new Bun.Glob("**.html").scanSync("src"))
    .map((a) => path.resolve("src", a))
    .filter((dir) => !dir.includes("node_modules"));

  console.log(
    `📄 Found ${entrypoints.length} HTML ${
      entrypoints.length === 1 ? "file" : "files"
    } to process\n`,
  );

  const result = await build({
    entrypoints,
    outdir,
    plugins: [plugin],
    minify: true,
    target: "browser",
    sourcemap: "linked",
    define: {
      "process.env.NODE_ENV": JSON.stringify("production"),
    },
    ...cliConfig,
  });

  const end = performance.now();

  const outputTable = result.outputs.map((output) => ({
    File: path.relative(process.cwd(), output.path),
    Type: output.kind,
    Size: formatFileSize(output.size),
  }));

  console.table(outputTable);
  const buildTime = (end - start).toFixed(2);

  console.log(`\n✅ Build completed in ${buildTime}ms\n`);
}

main();
