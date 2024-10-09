import '../styles/global.css'
import { Inter } from 'next/font/google'
import { ThemeProvider } from '@/components/ui/theme-provider'
import { Toaster } from '@/components/ui/toaster'
import Navbar from '@/components/ui/Navbar'
import { AuthProvider } from '@/components/AuthContext'
import Image from 'next/image'
import Link from 'next/link'
import logotype from '../assets/freelpay_logo.png'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Freelpay - Get Paid Instantly',
  description: 'Freelpay helps freelancers get paid as soon as the invoice is created.',
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-gradient-to-b from-background to-secondary min-h-screen`}>
        <AuthProvider>
          <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
            <Navbar />
            <main className="container mx-auto py-8 px-4 md:px-8">
              {children}
            </main>
            <footer className="container mx-auto py-6 px-4 md:px-8 text-center text-sm text-muted-foreground border-t border-border/40">
              © 2024 Freelpay - All rights reserved.
            </footer>
            <Toaster />
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  )
}