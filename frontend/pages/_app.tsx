import { Toaster } from "@/components/ui/toaster";
import { DateContextProvider } from "@/contexts/DateContext";
import "@/styles/globals.css";
import type { AppProps } from "next/app";
import Head from "next/head";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
     <DateContextProvider>
      <Head>
        <title>Buffalogs</title>
        <meta name="viewport" content="initial-scale=1, width=device-width" />
        BuffaLogs is an Open Source Django Project whose main purpose is to
        detect login anomalies
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Component {...pageProps} />
      <Toaster />
      </DateContextProvider>
    </>
  );
}
