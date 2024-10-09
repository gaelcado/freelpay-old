"use client"

import { Facebook, Twitter, Instagram, Linkedin } from 'lucide-react'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useTheme } from 'next-themes'
import Image from 'next/image'
import dynamic from 'next/dynamic'

const DynamicLogo = dynamic(() => import('@/components/ui/DynamicLogo'), { ssr: false })

export default function Footer() {
  return (
    <footer className="border-t py-12 px-4 md:px-8">
      <div className="container mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
          <div className="mb-6 md:mb-0 max-w-2xl">
            <div className="mb-4">
              <DynamicLogo width={100} height={32} />
            </div>
              <p className="text-muted-foreground">
                Helps you manage your business by paying you instantly or allows you to immobilize funds and earn interest.
              </p>
          </div>
          <div className="flex flex-col space-y-4">
            <h3 className="font-semibold">Subscribe to our newsletter</h3>
            <div className="flex space-x-2">
              <Input 
                type="email" 
                placeholder="Email" 
              />
              <Button>
                Subscribe
              </Button>
            </div>
          </div>
        </div>
        <div className="flex justify-start md:justify-between items-center flex-wrap">
          <div className="flex space-x-4 mb-4 md:mb-0">
            <a href="#" className="text-muted-foreground hover:text-foreground">
              <Facebook size={24} />
            </a>
            <a href="#" className="text-muted-foreground hover:text-foreground">
              <Twitter size={24} />
            </a>
            <a href="#" className="text-muted-foreground hover:text-foreground">
              <Instagram size={24} />
            </a>
            <a href="#" className="text-muted-foreground hover:text-foreground">
              <Linkedin size={24} />
            </a>
          </div>
          <p className="text-sm text-muted-foreground">
            © 2024 Freelpay - All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}