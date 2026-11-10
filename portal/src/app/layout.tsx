import type { Metadata } from "next";
import { Public_Sans } from "next/font/google";
import { GovBar } from "@/components/layout/GovBar";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import "@/styles/globals.css";

const publicSans = Public_Sans({
  subsets: ["latin"],
  variable: "--font-public-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SOSP • Sistema de Orientação para Serviços Públicos",
  description:
    "Plataforma acadêmica de orientação, checklist de documentos e agendamento presencial para serviços públicos de Alagoas. Projeto desenvolvido por estudantes de Engenharia de Software do CESMAC.",
  keywords: ["serviços públicos", "agendamento", "documentos", "RG", "CIN", "CNH", "Alagoas", "Maceió", "CESMAC"],
  authors: [{ name: "CESMAC - Engenharia de Software" }],
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
    ],
  },
  openGraph: {
    title: "SOSP • Sistema de Orientação para Serviços Públicos",
    description: "Plataforma acadêmica de orientação, checklist de documentos e agendamento presencial. Projeto CESMAC.",
    siteName: "SOSP",
    locale: "pt_BR",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" className={publicSans.variable}>
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Public+Sans:ital,wght@0,300..900;1,300..900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={`${publicSans.className} font-sans min-h-screen flex flex-col justify-between bg-[#F8FAFC]`}>
        {/* Skip Link para acessibilidade eMAG / WCAG 2.1 AA */}
        <a href="#conteudo-principal" className="sosp-skip-link">
          Pular para o conteúdo principal
        </a>

        <div>
          <GovBar />
          <Header />
          <main id="conteudo-principal" tabIndex={-1} className="focus:outline-none">
            {children}
          </main>
        </div>

        <Footer />
      </body>
    </html>
  );
}
