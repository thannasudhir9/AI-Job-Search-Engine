import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import { Toaster } from "sonner";
import ThemeToggle from "./components/ThemeToggle";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Job Search Engine",
  description: "Find matching jobs, tailor your resume, track applications - locally.",
};

const nav = [
  { href: "/", label: "Job Search Engine" },
  { href: "/applied", label: "Applied" },
  { href: "/tracker", label: "Tracker" },
  { href: "/sources", label: "Sources" },
  { href: "/profile", label: "Profile & Resume" },
  { href: "/docs", label: "Docs" },
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`} suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `try{var t=localStorage.getItem('theme')||'light';if(t==='dark')document.documentElement.classList.add('dark')}catch(e){}`,
          }}
        />
      </head>
      <body className="min-h-full flex flex-col">
        <header
          className="border-b backdrop-blur sticky top-0 z-10"
          style={{ background: "var(--header-bg)", borderColor: "var(--brd)" }}
        >
          <div className="mx-auto max-w-7xl px-6 h-14 flex items-center gap-8">
            <Link href="/" className="font-bold tracking-tight">
              🎯 AI Job Search Engine
            </Link>
            <nav className="flex gap-1 text-sm flex-1">
              {nav.map((n) => (
                <Link key={n.href} href={n.href} className="nav-link">
                  {n.label}
                </Link>
              ))}
            </nav>
            <ThemeToggle />
          </div>
        </header>
        <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-8">{children}</main>
        <footer className="border-t py-5 text-center text-sm" style={{ borderColor: "var(--brd)" }}>
          <p>
            Developed with <span className="text-red-500">❤</span> by{" "}
            <span className="font-medium">Sudhir Kumar Thanna</span>
          </p>
          <p className="muted text-xs mt-1">© 2026 Sudhir Kumar Thanna. All rights reserved.</p>
        </footer>
        <Toaster richColors position="bottom-right" />
      </body>
    </html>
  );
}
