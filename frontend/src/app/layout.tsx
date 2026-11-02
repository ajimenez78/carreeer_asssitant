import type { Metadata } from "next";
import { I18nProvider } from "../lib/i18n/provider";
import { AppShell } from "../components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Your ideal job | Career assistant",
  description: "Define what matters in your next role, from responsibilities to work–life balance.",
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
