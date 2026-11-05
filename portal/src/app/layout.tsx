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
  weight: ["300", "400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "SOSP — Sistema de Orientação para Serviços Públicos",
  description:
    "Portal oficial de orientação, checklist de documentos e agendamento presencial para serviços públicos de Alagoas.",
  keywords: ["serviços públicos", "agendamento", "documentos", "RG", "CNH", "Alagoas", "Maceió"],
  authors: [{ name: "CESMAC - Engenharia de Software" }],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" className={publicSans.variable}>
      <head>
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
