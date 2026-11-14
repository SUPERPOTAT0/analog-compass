import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Analog Compass",
  description: "Test-led Earth-analogue finder for Moon/Mars field campaigns.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
