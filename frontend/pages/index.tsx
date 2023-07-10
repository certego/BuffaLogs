import Image from "next/image";
import { Inter } from "next/font/google";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/router";

const inter = Inter({ subsets: ["latin"] });

export default function Home() {
  const router = useRouter();
  return (
    <main>
      <div className="flex flex-row justify-between mx-10 my-10">
        <div className="text-left">
          <h1 className="text-5xl font-bold">Buffalogs</h1>
          <p className="pt-1 text-sm opacity-75"></p>
        </div>
        <Button
          onClick={() => {
            router.push("/auth");
          }}
          className="z-50"
        >
          Login
        </Button>
      </div>
      <div className="fixed top-0 left-0 h-screen w-screen flex flex-col items-center justify-center">
        <h1 className="w-[80%] text-4xl font-SpaceGrotesk text-center leading-relaxed">
          An Open Source Django Project whose main<br/> purpose is to detect login
          anomalies.
        </h1>
        <Image
          src="/worldmap.png"
          width={800}
          height={200}
          className=" opacity-60 mt-12"
          alt="map"
        ></Image>
      </div>
    </main>
  );
}
