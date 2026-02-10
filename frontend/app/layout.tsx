import './output.css';
import { Inter } from 'next/font/google';
import { Toaster } from 'sonner';
import Header from '../components/Header';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
    title: 'Treno Web',
    description: 'Instant Train Search',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className={`${inter.className} antialiased bg-slate-50 text-slate-900 overflow-x-hidden flex flex-col min-h-screen`}>
                <Header />
                <div className="flex-grow">
                    {children}
                </div>
                <Toaster richColors position="top-center" />
            </body>
        </html>
    );
}
