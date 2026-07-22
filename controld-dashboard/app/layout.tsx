import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Control D Dashboard",
  description: "Local dashboard for your Control D DNS account",
};

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/profiles", label: "Profiles" },
  { href: "/devices", label: "Devices" },
  { href: "/ips", label: "Known IPs" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen flex flex-col">
          <header className="border-b border-gray-200 dark:border-neutral-800">
            <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-6">
              <span className="font-semibold text-lg">Control D Dashboard</span>
              <nav className="flex gap-4 text-sm">
                {NAV.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
            </div>
          </header>
          <main className="max-w-5xl mx-auto w-full px-4 py-6 flex-1">{children}</main>
          <footer className="max-w-5xl mx-auto w-full px-4 py-4 text-xs text-gray-400">
            Data refreshes on every page load. Control D&apos;s public API does not
            expose DNS query logs or traffic analytics — only account/profile/device
            configuration and known IPs.
          </footer>
        </div>
      </body>
    </html>
  );
}
