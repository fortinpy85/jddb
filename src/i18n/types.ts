/**
 * TypeScript type definitions for i18next
 */

export type SupportedLanguage = "en" | "fr";

export interface I18nNamespace {
  common: typeof import("@/locales/en/common.json");
  jobs: typeof import("@/locales/en/jobs.json");
  errors: typeof import("@/locales/en/errors.json");
  navigation: typeof import("@/locales/en/navigation.json");
  dashboard: typeof import("@/locales/en/dashboard.json");
  upload: typeof import("@/locales/en/upload.json");
  forms: typeof import("@/locales/en/forms.json");
}

declare module "i18next" {
  interface CustomTypeOptions {
    defaultNS: "common";
    resources: I18nNamespace;
  }
}
