'use client'

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"

export default function NavBar() {
  const pathname = usePathname()
  const [menuOpen, setMenuOpen] = useState(false)

  const linkClass = (path: string) =>
    pathname === path
      ? "font-semibold text-black"
      : "text-gray-700 hover:text-black transition"

  const handleLinkClick = () => {
    setMenuOpen(false)
  }

  return (
    <nav className="fixed top-0 z-50 w-full bg-white border-b border-[#D9D9D9]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="h-[72px] flex items-center justify-between">

          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <img
              src="/images/PanAfricanReport_logo.png"
              alt="PanAfricanReport"
              className="h-10 w-auto"
            />
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex gap-6 text-[15px]">
            <Link href="/" className={linkClass("/")}>Home</Link>
            <Link href="/about" className={linkClass("/about")}>About</Link>
            <Link href="/contact" className={linkClass("/contact")}>Contact</Link>
            <Link href="/privacy-policy" className={linkClass("/privacy-policy")}>Privacy Policy</Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden flex items-center justify-center w-10 h-10 rounded-md hover:bg-gray-100 transition"
            aria-label="Toggle menu"
          >
            <span className="text-2xl">
              {menuOpen ? "✕" : "☰"}
            </span>
          </button>
        </div>

        {/* Mobile Dropdown */}
        {menuOpen && (
        <div className="md:hidden text-center border-t border-gray-200 py-4 space-y-3">
          <Link
            href="/"
            onClick={handleLinkClick}
            className={`block ${linkClass("/")}`}
          >
            Home
          </Link>

          <Link
            href="/about"
            onClick={handleLinkClick}
            className={`block ${linkClass("/about")}`}
          >
            About
          </Link>

          <Link
            href="/contact"
            onClick={handleLinkClick}
            className={`block ${linkClass("/contact")}`}
          >
            Contact
          </Link>

          <Link
            href="/privacy-policy"
            onClick={handleLinkClick}
            className={`block ${linkClass("/privacy-policy")}`}
          >
            Privacy Policy
          </Link>
        </div>
      )}

      </div>
    </nav>
  )
}
