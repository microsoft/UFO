import React, { ChangeEvent } from 'react';
import { Filter, Search } from 'lucide-react';
import clsx from 'clsx';
import { MessageKind, useGalaxyStore } from '../../store/galaxyStore';
import { shallow } from 'zustand/shallow';

const MESSAGE_FILTERS: Array<{ label: string; value: MessageKind | 'all' }> = [
  { label: 'All', value: 'all' },
  { label: 'Responses', value: 'response' },
  { label: 'User', value: 'user' },
];

const SearchFilterBar: React.FC = () => {
  const { searchQuery, messageKindFilter, setSearchQuery, setMessageKindFilter } =
    useGalaxyStore(
      (state) => ({
        searchQuery: state.ui.searchQuery,
        messageKindFilter: state.ui.messageKindFilter,
        setSearchQuery: state.setSearchQuery,
        setMessageKindFilter: state.setMessageKindFilter,
      }),
      shallow,
    );

  const handleSearchChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
  };

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-white/5 bg-galaxy-midnight/80 p-4 shadow-inset backdrop-blur">
      <div className="flex items-center gap-3 rounded-xl border border-white/5 bg-black/20 px-3 py-2">
        <Search className="h-4 w-4 text-slate-400" aria-hidden />
        <input
          type="search"
          value={searchQuery}
          onChange={handleSearchChange}
          placeholder="Search messages, tasks, or devices"
          className="w-full bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
        />
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="flex items-center gap-1 rounded-full border border-white/5 bg-white/5 px-2 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-300">
          <Filter className="h-3 w-3" aria-hidden />
          Filter
        </span>
        {MESSAGE_FILTERS.map(({ label, value }) => (
          <button
            key={value}
            type="button"
            className={clsx(
              'rounded-full px-3 py-1 transition-colors',
              messageKindFilter === value
                ? 'bg-gradient-to-r from-galaxy-blue to-galaxy-purple text-white shadow-glow'
                : 'border border-white/10 bg-white/5 text-slate-300 hover:border-white/20 hover:text-white',
            )}
            onClick={() => setMessageKindFilter(value)}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default SearchFilterBar;
