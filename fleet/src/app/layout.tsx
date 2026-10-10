import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Správa vozidiel", template: "%s · Správa vozidiel" },
  description: "Rezervácie, prevzatie a doklady firemných áut",
  applicationName: "Správa vozidiel",
  appleWebApp: { capable: true, title: "Vozidlá", statusBarStyle: "default" },
};

export const viewport: Viewport = {
  themeColor: "#1d4ed8",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="sk" className="h-full antialiased">
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}
