import type { Metadata } from "next";
import { I18nProvider } from "../lib/i18n/provider";
import { AppShell } from "../components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "The role you’re looking for | Career assistant",
  description: "Clarify what you’re looking for in a role, from responsibilities to work–life balance.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <I18nProvider><AppShell>{children}</AppShell></I18nProvider>
      </body>
    </html>
  );
}
