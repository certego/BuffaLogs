import { NextRequest, NextResponse } from "next/server";

export function middleware(request: NextRequest) {
  const cookie = request.cookies.get('user');
  console.log(cookie, "uahdasd")

  if (cookie === undefined && request.url.includes('/dashboard')) {
    return NextResponse.redirect(new URL('/auth', request.url));}
    else if(cookie !== undefined && request.url.includes('/auth')){
      return NextResponse.redirect(new URL('/dashboard', request.url))
    }
    else {
    return NextResponse.next();
    }  
}

