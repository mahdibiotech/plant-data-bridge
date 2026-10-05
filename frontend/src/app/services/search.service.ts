import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { SearchResponse } from '../models/search-response.model';

export interface SearchFilters {
  q?: string;
  source?: string;
  crop?: string;
  country?: string;
  studyType?: string;
  program?: string;

  page?: number;
  size?: number;

  sort?: string;
  order?: string;
}

@Injectable({
  providedIn: 'root',
})
export class SearchService {
  private readonly http = inject(HttpClient);

  private readonly apiUrl = '/api/search';

  search(
    filters: SearchFilters,
  ): Observable<SearchResponse> {

    let params = new HttpParams();

    if (filters.q) {
      params = params.set('q', filters.q);
    }

    if (filters.source) {
      params = params.set('source', filters.source);
    }

    if (filters.crop) {
      params = params.set('crop', filters.crop);
    }

    if (filters.country) {
      params = params.set('country', filters.country);
    }

    if (filters.studyType) {
      params = params.set(
        'studyType',
        filters.studyType,
      );
    }

    if (filters.program) {
      params = params.set(
        'program',
        filters.program,
      );
    }

    params = params
      .set('page', String(filters.page ?? 0))
      .set('size', String(filters.size ?? 10))
      .set('sort', filters.sort ?? 'relevance')
      .set('order', filters.order ?? 'desc');

    return this.http.get<SearchResponse>(
      this.apiUrl,
      { params },
    );
  }
}
