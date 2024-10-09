"use client"

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { NavigationMenu, NavigationMenuItem, NavigationMenuLink, NavigationMenuList, navigationMenuTriggerStyle } from "@/components/ui/navigation-menu"
import { Menu } from 'lucide-react'
import { ModeToggle } from '@/components/mode-toggle'
import Image from 'next/image'
import { useAuth } from '@/components/AuthContext'
import { useToast } from "@/components/ui/use-toast"

export default function Navbar() {
  const pathname = usePathname()
  const router = useRouter()
  const { isAuthenticated, setIsAuthenticated } = useAuth()
  const { toast } = useToast()

  const routes = [
    { href: '/new-invoice', label: 'New Invoice', requireAuth: false },
    { href: '/profile', label: 'My Profile', requireAuth: true },
    { href: '/dashboard', label: 'My Dashboard', requireAuth: true },
  ]

  const filteredRoutes = routes.filter(route => !route.requireAuth || isAuthenticated)

  const handleLogout = () => {
    localStorage.removeItem('token')
    setIsAuthenticated(false)
    toast({
      title: "Logged out",
      description: "You have been successfully logged out.",
    })
    router.push('/')
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between">
        <div className="flex items-center">
          <Link href="/" className="mr-6 flex items-center space-x-2">
            <Image
              src="/assets/freelpay_logo.png"
              alt="Freelpay Logo"
              width={100}
              height={32}
            />
          </Link>
          <NavigationMenu className="hidden md:flex">
            <NavigationMenuList>
              {filteredRoutes.map((route) => (
                <NavigationMenuItem key={route.href}>
                  <Link href={route.href} legacyBehavior passHref>
                    <NavigationMenuLink className={navigationMenuTriggerStyle()} active={pathname === route.href}>
                      {route.label}
                    </NavigationMenuLink>
                  </Link>
                </NavigationMenuItem>
              ))}
            </NavigationMenuList>
          </NavigationMenu>
        </div>
        <div className="flex items-center space-x-4">
          <ModeToggle />
          {!isAuthenticated ? (
            <Link href="/">
              <Button variant="outline">Login</Button>
            </Link>
          ) : (
            <Button variant="outline" onClick={handleLogout}>
              Logout
            </Button>
          )}
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" className="md:hidden">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent position="left">
              <nav className="flex flex-col space-y-4">
                {filteredRoutes.map((route) => (
                  <Link
                    key={route.href}
                    href={route.href}
                    className={`text-sm font-medium transition-colors hover:text-primary ${
                      pathname === route.href ? 'text-black dark:text-white' : 'text-muted-foreground'
                    }`}
                  >
                    {route.label}
                  </Link>
                ))}
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  )
}