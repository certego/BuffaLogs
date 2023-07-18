"use client"

import { logoutUser } from "@/lib/auth";

import { Button } from "./ui/button";
import { DatePickerWithRange } from "./DatePicker";
import Link from "next/link";
import { useRouter } from "next/router";

const Header: React.FC = () => {
  const router = useRouter();
    return(
        <>
        <div className=" flex flex-row justify-between mx-10 h-[10%] mt-10">
        <span className="flex flex-row items-end space-x-7">
          <Link href="/">
            <div className="text-left">
              <h1 className="text-4xl font-bold">Buffalogs</h1>
              <p className="pt-1 text-md opacity-75">Detect Login anomalies.</p>
            </div>
          </Link>
          <DatePickerWithRange />
        </span>
        <Button
          onClick={async () => {
            const push = await logoutUser();
            router.push("/auth");
          }}
        >
          Logout
        </Button>
      </div>
      </>
    );
}

export default Header;