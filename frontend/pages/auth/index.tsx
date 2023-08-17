"use client";
import { useCookies } from "react-cookie";
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
import { loginUser } from "@/lib/auth";
import { useEffect, useState } from "react";
import { removeToken } from "@/lib/token";
import { toast } from "@/components/ui/use-toast";


const formSchema = z.object({
  email: z.string().min(2, {
    message: "Email must be at least 6 characters.",
  }),
  Password: z.string().min(2, {
    message: "Password must be at least 6 characters.",
  }),
});

export default function Auth() {
  const [errorMessage, setErrorMessage] = useState("");
  const [cookie, setCookie] = useCookies(['user']);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter()

  useEffect(() => {
    removeToken();
  }, []);
  
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      Password: "",
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      const data = await loginUser(values.email, values.Password)
      if (data && data.tokens) {
        console.log("kjahnasfn")
        setCookie("user", JSON.stringify(data), {
          path: "/",
          maxAge: 3600,
          sameSite: true,
        });
        toast({
          title: "Success!",
          description: "Redirecting to dashboard.",
        })
        setTimeout(() => {
          router.push(to_forward);
        }, 1000);
      const to_forward = "/dashboard/";
      setIsLoading(true);
      } else {
        setErrorMessage("Invalid Credentials!");
        toast({
          title: "Uh oh! Something went wrong.",
          description: "There was a problem with your authentication request.",
        })
      }
    } catch (error) {
    } finally {
      setIsLoading(false);
    }
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
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input placeholder="Enter your Email" {...field} />
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
                        <Input type="password" placeholder="Enter your Password" {...field} />
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
                Redirect to Home?
              </Link>
            </form>
          </Form>
        </div>
      </div>
    </main>
  );
}
