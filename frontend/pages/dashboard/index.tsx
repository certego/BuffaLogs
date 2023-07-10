import { DatePickerWithRange } from "@/components/DatePicker";
import { Button } from "@/components/ui/button";
import { logoutUser } from "@/lib/auth";
import Link from "next/link";
import { useRouter } from "next/router";

export default function Dashboard() {
  const router = useRouter();
  return (
    <>
      <div className="flex flex-row justify-between mx-10 my-10">
        <span className="flex flex-row items-end space-x-7">
          <Link href="/">
            <div className="text-left">
              <h1 className="text-3xl font-bold">Buffalogs</h1>
              <p className="pt-1 text-sm opacity-75">Detect Login anomalies.</p>
            </div>
          </Link>
          <DatePickerWithRange />
        </span>
        <Button
          onClick={async () => {
            const bleh = await logoutUser();
            router.push("/auth");
          }}
        >
          Logout
        </Button>
      </div>
      <main className="mx-20">
      </main>
    </>
  );
}
