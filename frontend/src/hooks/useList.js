import { useInfiniteQuery } from "@tanstack/react-query";
import { listResources } from "@/services/listResources";

/**
 * useList({ resource, params, enabled })
 * resource: 'hotels' | 'rooms' | 'reservations' | 'countries' | ...
 * params: filtros DRF (hotel, search, page_size, etc.)
 */
export const useList = ({ resource, params = {}, enabled = true }) => {
  const {
    data,
    isError,
    isPending,
    isSuccess,
    fetchNextPage,
    refetch,
    hasNextPage,
    isRefetching,
  } = useInfiniteQuery({
    queryKey: [resource, params],
    queryFn: listResources,
    getNextPageParam: (lastPage) => lastPage?.next_page ?? undefined,
    enabled,
  });

  const pages = data?.pages || [];
  const results = pages.length ? pages.flatMap((p) => p?.results ?? []) : [];
  const count = pages[0]?.count ?? 0;

  return {
    refetch,
    fetchNextPage,
    isSuccess,
    isPending,
    isRefetching,
    isError,
    results,
    count,
    hasNextPage,
    raw: pages[0]?.raw,
  };
};