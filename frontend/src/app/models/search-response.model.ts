import { Study } from './study.model';

export interface SearchHit {
  id: string;
  score: number;
  source: Study;
}

export interface SearchResponse {
  query: string;

  filters: {
    source?: string;
    crop?: string;
    country?: string;
    studyType?: string;
    program?: string;
  };

  page: number;
  size: number;

  total: number;
  totalPages: number;

  sort: string;
  order: string;

  results: SearchHit[];
}
