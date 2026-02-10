'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { MagnifyingGlassIcon } from '@heroicons/react/20/solid';
import { toast } from 'sonner';
import StationCombobox from './StationCombobox';

export default function SearchWidget() {
    const router = useRouter();
    const [selectedFrom, setSelectedFrom] = useState<any>(null);
    const [selectedTo, setSelectedTo] = useState<any>(null);
    const [date, setDate] = useState('');

    const handleSearch = () => {
        if (!selectedFrom || !selectedTo || !date) {
            toast.error("Please select stations and date");
            return;
        }

        if (selectedFrom.station_code === selectedTo.station_code) {
            toast.error("Source and destination cannot be the same");
            return;
        }

        const params = new URLSearchParams({
            from: selectedFrom.station_code,
            to: selectedTo.station_code,
            date: date,
        });
        router.push(`/search?${params.toString()}`);
    };

    return (
        <div suppressHydrationWarning className="w-full max-w-md mx-auto bg-white/80 backdrop-blur-md rounded-2xl p-6 shadow-xl border border-white/50">
            <div className="space-y-4">
                <StationCombobox
                    label="From"
                    selected={selectedFrom}
                    onChange={setSelectedFrom}
                />

                <StationCombobox
                    label="To"
                    selected={selectedTo}
                    onChange={setSelectedTo}
                />

                {/* Date Picker (Native for now) */}
                <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1 uppercase tracking-wider">Date</label>
                    <input
                        type="date"
                        className="w-full bg-slate-100 border-none rounded-lg p-3 text-slate-800 focus:ring-2 focus:ring-indigo-500"
                        value={date}
                        onChange={(e) => setDate(e.target.value)}
                    />
                </div>

                <button
                    onClick={handleSearch}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-xl shadow-lg shadow-indigo-200 transition-all transform hover:scale-[1.02] flex items-center justify-center gap-2"
                >
                    <MagnifyingGlassIcon className="h-5 w-5" />
                    Find Trains
                </button>
            </div>
        </div>
    );
}
