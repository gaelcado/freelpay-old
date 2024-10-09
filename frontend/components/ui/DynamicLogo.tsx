import { useTheme } from 'next-themes'
import Image from 'next/image'
import logoDark from '../../public/assets/logo_freelpay.png'
import logoLight from '../../public/assets/logo_freelpay_black.png'

interface DynamicLogoProps {
  width: number
  height: number
}

export default function DynamicLogo({ width, height }: DynamicLogoProps) {
  const { theme } = useTheme()
  return (
    <Image
      src={theme === 'dark' ? logoDark : logoLight}
      alt="Freelpay Logo"
      width={width}
      height={height}
    />
  )
}