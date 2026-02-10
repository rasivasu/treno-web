'use client';

import { Fragment, useState, useEffect } from 'react';
import { Combobox, Transition } from '@headlessui/react';
import { CheckIcon, ChevronUpDownIcon } from '@heroicons/react/20/solid';
import { toast } from 'sonner';

export interface Station {
    station_code: string;
    station_name: string;
}

interface StationComboboxProps {
    label: string;
    selected: Station | null;
    onChange: (station: Station) => void;
}

export default function StationCombobox({ label, selected, onChange }: StationComboboxProps) {
    const [query, setQuery] = useState('');
    const [stations, setStations] = useState<Station[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        const fetchStations = async () => {
            if (query.length < 2) {
                setStations([]);
                return;
            }
            setIsLoading(true);
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const response = await fetch(`${apiUrl}/api/stations?q=${query}`);
                if (response.ok) {
                    const data = await response.json();
                    setStations(data);
                } else {
                    // Silent failure for autocomplete is usually better, but we can log it
                    console.warn("API returned error");
                }
            } catch (error) {
                console.error("Failed to fetch stations", error);
                setStations([]);
                // Only toast on hard network error if user is actively typing? 
                // Maybe too noisy. Let's keep it silent for debounce but log it.
            } finally {
                setIsLoading(false);
            }
        };

        const timeoutId = setTimeout(fetchStations, 300);
        return () => clearTimeout(timeoutId);
    }, [query]);

    return (
        <div className="relative">
            <label className="block text-xs font-medium text-slate-500 mb-1 uppercase tracking-wider">
                {label}
            </label>
            <Combobox value={selected} onChange={onChange} nullable>
                <div className="relative mt-1">
                    <div className="relative w-full cursor-default overflow-hidden rounded-lg bg-white text-left shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-white/75 focus-visible:ring-offset-2 focus-visible:ring-offset-indigo-300 sm:text-sm">
                        <Combobox.Input
                            className="w-full border-none py-3 pl-3 pr-10 text-sm leading-5 text-slate-900 focus:ring-0"
                            displayValue={(station: Station | null) =>
                                station ? `${station.station_name} (${station.station_code})` : ''
                            }
                            onChange={(event) => setQuery(event.target.value)}
                            placeholder="Type station code or name..."
                        />
                        <Combobox.Button className="absolute inset-y-0 right-0 flex items-center pr-2">
                            <ChevronUpDownIcon
                                className="h-5 w-5 text-slate-400"
                                aria-hidden="true"
                            />
                        </Combobox.Button>
                    </div>
                    <Transition
                        as={Fragment}
                        leave="transition ease-in duration-100"
                        leaveFrom="opacity-100"
                        leaveTo="opacity-0"
                        afterLeave={() => setQuery('')}
                    >
                        <Combobox.Options className="absolute mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black/5 focus:outline-none sm:text-sm z-10">
                            {isLoading ? (
                                <div className="relative cursor-default select-none px-4 py-2 text-slate-500">
                                    Loading...
                                </div>
                            ) : stations.length === 0 && query !== '' ? (
                                <div className="relative cursor-default select-none px-4 py-2 text-slate-700">
                                    Nothing found.
                                </div>
                            ) : (
                                stations.map((station) => (
                                    <Combobox.Option
                                        key={station.station_code}
                                        className={({ active }) =>
                                            `relative cursor-default select-none py-2 pl-10 pr-4 ${active ? 'bg-indigo-600 text-white' : 'text-slate-900'
                                            }`
                                        }
                                        value={station}
                                    >
                                        {({ selected, active }) => (
                                            <>
                                                <span
                                                    className={`block truncate ${selected ? 'font-medium' : 'font-normal'
                                                        }`}
                                                >
                                                    {station.station_name} ({station.station_code})
                                                </span>
                                                {selected ? (
                                                    <span
                                                        className={`absolute inset-y-0 left-0 flex items-center pl-3 ${active ? 'text-white' : 'text-indigo-600'
                                                            }`}
                                                    >
                                                        <CheckIcon className="h-5 w-5" aria-hidden="true" />
                                                    </span>
                                                ) : null}
                                            </>
                                        )}
                                    </Combobox.Option>
                                ))
                            )}
                        </Combobox.Options>
                    </Transition>
                </div>
            </Combobox>
        </div>
    );
}
