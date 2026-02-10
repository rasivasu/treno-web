'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Header() {
    const pathname = usePathname();

    const navLink = {
        href: pathname === '/' ? '/search' : '/',
        text: pathname === '/' ? 'Search' : 'Home'
    };

    return (
        <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur px-6 py-3 flex items-center justify-between">
            <div className="flex items-center">
                <Link href="/" className="text-xl font-bold text-slate-900 hover:text-indigo-600 transition-colors">
                    Treno Web
                </Link>
            </div>
            <nav className="flex items-center gap-6">
                <Link href={navLink.href} className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
                    {navLink.text}
                </Link>
                <Link href="/privacy" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
                    Privacy
                </Link>
            </nav>
        </header>
    );
}
