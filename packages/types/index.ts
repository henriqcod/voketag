/**
 * Tipos compartilhados - re-exporta tipos gerados a partir de OpenAPI
 * Atualizar: cd packages/types && npm run generate
 */
import type { components } from "./generated/scan";
export type { components, paths } from "./generated/scan";
export type ScanResult = components["schemas"]["ScanResult"];
