import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Your ideal job | Career assistant",
  description: "Define what matters in your next role, from responsibilities to work–life balance.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">Skip to content</a>
        <header className="site-header">
          <div className="header-inner">
            <Link className="brand" href="/">Career assistant</Link>
            <nav aria-label="Main navigation">
              <Link className="nav-link" href="/" aria-current="page">Job definition</Link>
            </nav>
          </div>
        </header>
        {children}
        <footer className="site-footer">A clearer direction for your next role.</footer>
      </body>
    </html>
  );
}
