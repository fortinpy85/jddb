/**
 * TypeScript type definitions for i18next
 */

export type SupportedLanguage = "en" | "fr";

export interface I18nNamespace {
  common: typeof import("@/locales/en/common.json");
  jobs: typeof import("@/locales/en/jobs.json");
  errors: typeof import("@/locales/en/errors.json");
  navigation: typeof import("@/locales/en/navigation.json");
}

declare module "i18next" {
  interface CustomTypeOptions {
    defaultNS: "common";
    resources: I18nNamespace;
  }
}
