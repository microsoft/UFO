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
    <div className="flex flex-col gap-3 rounded-[24px] border border-white/10 bg-gradient-to-br from-[rgba(11,30,45,0.85)] via-[rgba(8,20,35,0.82)] to-[rgba(6,15,28,0.85)] p-4 shadow-[0_8px_32px_rgba(0,0,0,0.35),0_2px_8px_rgba(15,123,255,0.1),inset_0_1px_1px_rgba(255,255,255,0.06)] ring-1 ring-inset ring-white/5">
      <div className="flex items-center gap-3 rounded-xl border border-white/5 bg-gradient-to-r from-black/30 to-black/20 px-3 py-2.5 shadow-[inset_0_2px_8px_rgba(0,0,0,0.3)] focus-within:border-white/15 focus-within:shadow-[0_0_8px_rgba(15,123,255,0.08),inset_0_2px_8px_rgba(0,0,0,0.3)]">
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
        <span className="flex items-center gap-1 rounded-full border border-white/10 bg-white/10 px-2.5 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-300 shadow-[inset_0_1px_2px_rgba(255,255,255,0.1)]">
          <Filter className="h-3 w-3" aria-hidden />
          Filter
        </span>
        {MESSAGE_FILTERS.map(({ label, value }) => (
          <button
            key={value}
            type="button"
            className={clsx(
              'rounded-full px-3 py-1.5 transition-all duration-200',
              messageKindFilter === value
                ? 'bg-gradient-to-r from-galaxy-blue to-galaxy-purple text-white shadow-[0_0_20px_rgba(15,123,255,0.4),0_2px_8px_rgba(123,44,191,0.3)] ring-1 ring-white/20'
                : 'border border-white/10 bg-white/5 text-slate-300 shadow-[inset_0_1px_2px_rgba(255,255,255,0.05)] hover:border-white/20 hover:bg-white/10 hover:text-white hover:shadow-[0_0_10px_rgba(15,123,255,0.15)]',
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
