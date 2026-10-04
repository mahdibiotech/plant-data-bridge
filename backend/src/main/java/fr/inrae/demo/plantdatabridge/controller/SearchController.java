package fr.inrae.demo.plantdatabridge.controller;

import co.elastic.clients.elasticsearch.ElasticsearchClient;
import co.elastic.clients.elasticsearch._types.SortOrder;
import co.elastic.clients.elasticsearch._types.query_dsl.BoolQuery;
import co.elastic.clients.elasticsearch.core.SearchRequest;
import co.elastic.clients.elasticsearch.core.SearchResponse;
import co.elastic.clients.elasticsearch.core.search.Hit;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;


@RestController
@RequestMapping("/api")
public class SearchController {

    private final ElasticsearchClient client;
    private final String indexName;

    public SearchController(
            ElasticsearchClient client,
            @Value("${elasticsearch.index}") String indexName
    ) {
        this.client = client;
        this.indexName = indexName;
    }


    @GetMapping("/search")
    public ResponseEntity<Map<String, Object>> search(
            @RequestParam(defaultValue = "") String q,
            @RequestParam(required = false) String source,
            @RequestParam(required = false) String crop,
            @RequestParam(required = false) String country,
            @RequestParam(required = false) String studyType,
            @RequestParam(required = false) String program,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "relevance") String sort,
            @RequestParam(defaultValue = "desc") String order
    ) throws IOException {

        page = Math.max(page, 0);
        size = Math.max(1, Math.min(size, 100));

        boolean exists = client.indices()
                .exists(e -> e.index(indexName))
                .value();

        if (!exists) {
            Map<String, Object> response = new LinkedHashMap<>();

            response.put("query", q);
            response.put("page", page);
            response.put("size", size);
            response.put("total", 0);
            response.put("totalPages", 0);
            response.put("results", List.of());
            response.put(
                    "warning",
                    "Search index is not available"
            );

            return ResponseEntity.ok(response);
        }


        BoolQuery.Builder boolQuery = new BoolQuery.Builder();


        /*
         * Full-text query.
         *
         * Field boosts make study names and biological
         * descriptors more important than secondary metadata.
         */
        if (q != null && !q.isBlank()) {

            boolQuery.must(query -> query.multiMatch(multi -> multi
                    .query(q)
                    .fields(
                            "study_name^4",
                            "study_description^2",
                            "scientific_name^3",
                            "common_crop_name^3",
                            "traits^3",
                            "location_name^2",
                            "trial_name",
                            "program_name"
                    )
            ));

        } else {

            boolQuery.must(query -> query.matchAll(matchAll -> matchAll));
        }


        /*
         * Exact business filters.
         */
        if (hasValue(source)) {
            boolQuery.filter(query -> query.term(term -> term
                    .field("source")
                    .value(source)
            ));
        }

        if (hasValue(crop)) {
            boolQuery.filter(query -> query.term(term -> term
                    .field("common_crop_name")
                    .value(crop)
            ));
        }

        if (hasValue(country)) {
            boolQuery.filter(query -> query.term(term -> term
                    .field("country")
                    .value(country)
            ));
        }

        if (hasValue(studyType)) {
            boolQuery.filter(query -> query.term(term -> term
                    .field("study_type")
                    .value(studyType)
            ));
        }

        if (hasValue(program)) {
            boolQuery.filter(query -> query.term(term -> term
                    .field("program_name")
                    .value(program)
            ));
        }


        SearchRequest.Builder request = new SearchRequest.Builder()
                .index(indexName)
                .from(page * size)
                .size(size)
                .query(query -> query.bool(boolQuery.build()));


        /*
         * Sorting.
         *
         * relevance -> Elasticsearch score
         * studyName -> alphabetical study name
         * source    -> provider
         * country   -> country
         */
        SortOrder sortOrder = "asc".equalsIgnoreCase(order)
                ? SortOrder.Asc
                : SortOrder.Desc;

        switch (sort.toLowerCase()) {

            case "studyname" -> request.sort(s -> s.field(f -> f
                    .field("study_name.keyword")
                    .order(sortOrder)
            ));

            case "source" -> request.sort(s -> s.field(f -> f
                    .field("source")
                    .order(sortOrder)
            ));

            case "country" -> request.sort(s -> s.field(f -> f
                    .field("country")
                    .order(sortOrder)
            ));

            default -> request.sort(s -> s.score(score -> score
                    .order(sortOrder)
            ));
        }


        SearchResponse<Map> elasticResponse =
                client.search(request.build(), Map.class);


        List<Map<String, Object>> results = new ArrayList<>();

        for (Hit<Map> hit : elasticResponse.hits().hits()) {

            Map<String, Object> item = new LinkedHashMap<>();

            item.put("id", hit.id());
            item.put("score", hit.score());
            item.put("source", hit.source());

            results.add(item);
        }


        long total = elasticResponse.hits().total() != null
                ? elasticResponse.hits().total().value()
                : results.size();

        long totalPages = (long) Math.ceil(
                total / (double) size
        );


        Map<String, Object> filters = new LinkedHashMap<>();

        if (hasValue(source)) {
            filters.put("source", source);
        }

        if (hasValue(crop)) {
            filters.put("crop", crop);
        }

        if (hasValue(country)) {
            filters.put("country", country);
        }

        if (hasValue(studyType)) {
            filters.put("studyType", studyType);
        }

        if (hasValue(program)) {
            filters.put("program", program);
        }


        Map<String, Object> response = new LinkedHashMap<>();

        response.put("query", q);
        response.put("filters", filters);

        response.put("page", page);
        response.put("size", size);

        response.put("total", total);
        response.put("totalPages", totalPages);

        response.put("sort", sort);
        response.put("order", order);

        response.put("results", results);


        return ResponseEntity.ok(response);
    }


    private boolean hasValue(String value) {
        return value != null && !value.isBlank();
    }
}
