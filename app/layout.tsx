import "./globals.css";
import { Outfit } from "next/font/google";

const outfit = Outfit({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });

export const metadata = {
  title: "GLiNER2 Support Triage Demo",
  description: "Local GLiNER2 demo for schema-first extraction & routing"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={outfit.className}>{children}</body>
    </html>
  );
}
