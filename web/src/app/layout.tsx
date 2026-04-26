import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";

import { Providers } from "./providers";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter"
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display"
});

export const metadata: Metadata = {
  title: "DocuMind",
  description: "AI document intelligence with grounded answers, citations, and premium product UX."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${spaceGrotesk.variable} font-sans`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
