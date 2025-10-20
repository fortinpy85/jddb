interface Process {
  env?: {
    NEXT_PUBLIC_API_URL?: string;
    NEXT_PUBLIC_API_KEY?: string;
    NODE_ENV?: string;
  };
}

interface ImportMeta {
  env?: {
    VITE_API_KEY?: string;
  };
}

declare const process: Process | undefined;
declare const importmeta: ImportMeta | undefined;
