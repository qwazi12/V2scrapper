import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "Screen Central OS",
  description: "Private, evidence-led creative operations for Screen Central.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
