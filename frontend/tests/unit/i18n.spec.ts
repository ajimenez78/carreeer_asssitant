import { expect, test } from "@playwright/test";
import { english, isLocale, locales, spanish, translate } from "../../src/lib/i18n/catalogs";

test("locale catalogs provide complete messages and matching interpolation tokens", () => {
  const tokens = (s: string) => s.match(/\{\w+\}/g)?.sort() ?? [];
  for (const language of Object.values(locales)) {
    expect(Object.keys(language.messages).sort()).toEqual(Object.keys(english).sort());
    for (const [key, message] of Object.entries(language.messages)) {
      expect(message.trim()).not.toBe("");
      expect(tokens(message)).toEqual(tokens(key));
    }
  }
  expect(spanish["Save draft"]).toBe("Guardar borrador");
  expect(isLocale("en")).toBe(true); expect(isLocale("es")).toBe(true);
  expect(isLocale("fr")).toBe(false); expect(isLocale("__proto__")).toBe(false);
});

test("translation interpolates source names without translating user content", () => {
  expect(translate("es", "Background review: {name}", { name: "Save draft" })).toBe("Revisión de trayectoria: Save draft");
  expect(translate("es", "Custom CV text")).toBe("Custom CV text");
  expect(translate("es", "Mi criterio: keep the value within 4,000 characters.")).toBe("Mi criterio: limita el valor a 4.000 caracteres.");
  expect(translate("en", "Save draft")).toBe("Save draft");
});
