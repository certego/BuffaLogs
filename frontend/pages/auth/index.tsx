"use client";

import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/Form";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRouter } from "next/router";

const formSchema = z.object({
  username: z.string().min(2, {
    message: "Username must be at least 2 characters.",
  }),
  Password: z.string().min(2, {
    message: "Password must be at least 6 characters.",
  }),
});

export default function Auth() {
  const router = useRouter()
  
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
      Password: "",
    },
  });

  // 2. Define a submit handler.
  function onSubmit(values: z.infer<typeof formSchema>) {
    console.log(values);
    router.push('/')
  }

  return (
    <main className="h-screen flex items-center justify-center">
      <div className="md:w-2/4 max-w-lg items-center mx-12 rounded-2xl">
        <div className="text-left pb-8 mx-12 my-12">
          <h1 className="text-6xl font-bold">Buffalogs</h1>
          <p className="pt-1 opacity-75">Enter your Login Details</p>
        </div>
        <div id="form" className="mx-12 my-12">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
              <>
                <FormField
                  control={form.control}
                  name="username"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Username</FormLabel>
                      <FormControl>
                        <Input placeholder="Enter your Username" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="Password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Password</FormLabel>
                      <FormControl>
                        <Input placeholder="Enter your Password" {...field} />
                      </FormControl>

                      <FormMessage />
                    </FormItem>
                  )}
                />
              </>
              <Button type="submit" className="">
                Submit
              </Button>
              <Link href={"/"} className="ml-4 text-sm opacity-70 items-end underline underline-offset-2">
                Contact Support?
              </Link>
            </form>
          </Form>
        </div>
      </div>
    </main>
  );
}
