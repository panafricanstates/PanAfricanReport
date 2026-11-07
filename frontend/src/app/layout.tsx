// src/app/layout.tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono, Newsreader } from "next/font/google";
import "./globals.css";
import NavBar from "./_components/NavBar";
import { UBUNTU_REPORT_URL } from "@/utils/MyConstants";

const newsreader = Newsreader({
  variable: "--font-newsreader",
  subsets: ["latin"],
});

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Pan-African Report — Pan-African News & Perspectives",
    template: "%s | Pan-African Report",
  },
  description:
    "Pan-African Report is a pan-African news platform delivering trusted, balanced, and African-centered reporting from every country across the continent.",
  metadataBase: new URL(UBUNTU_REPORT_URL), // change to your real domain
  openGraph: {
    title: "Pan-African Report — Pan-African News & Perspectives",
    description:
      "News from every African country. African stories, told with context, dignity, and unity.",
    url: UBUNTU_REPORT_URL,
    siteName: "Pan-African Report",
    images: [
      {
        url: "/og/pan-african-report.png", // put this in /public/og/
        width: 1200,
        height: 630,
        alt: "Pan-African Report — Pan-African News",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Pan-African Report — Pan-African News & Perspectives",
    description:
      "All of Africa, one newsroom. Trusted reporting from across the continent.",
    images: ["/og/pan-african-report.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${newsreader.className} antialiased bg-[#FCF7F7]  `}
      >
        <NavBar />

        <div className="mt-[7rem] md:mt-[5rem]">
          <div className="max-w-7xl mx-auto md:px-8">
            {children}
          </div>
        </div>

        
      </body>
    </html>
  );
}
