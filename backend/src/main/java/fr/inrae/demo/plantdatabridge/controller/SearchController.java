package fr.inrae.demo.plantdatabridge.controller;

import co.elastic.clients.elasticsearch.ElasticsearchClient;
import co.elastic.clients.elasticsearch.core.SearchResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class SearchController {

    private final ElasticsearchClient client;

    @Value("${elasticsearch.index}")
    private String indexName;

    public SearchController(ElasticsearchClient client) {
        this.client = client;
    }

    @GetMapping("/search")
    public Map<String, Object> search(
        @RequestParam(defaultValue = "") String q
    ) throws IOException {

        boolean exists = client.indices()
            .exists(e -> e.index(indexName))
            .value();

        if (!exists) {
            return Map.of(
                "query", q,
                "total", 0,
                "results", List.of(),
                "warning", "Search index is not available"
            );
        }

        SearchResponse<Map> response = client.search(
            s -> s
                .index(indexName)
                .query(query -> {

                    if (q == null || q.isBlank()) {
                        return query.matchAll(m -> m);
                    }

                    return query.multiMatch(
                        m -> m
                            .query(q)
                            .fields(
                                "study_name^3",
                                "study_description^2",
                                "scientific_name^2",
                                "common_crop_name^2",
                                "traits^2",
                                "location_name",
                                "trial_name",
                                "program_name"
                            )
                    );
                }),
            Map.class
        );

        List<Map<String, Object>> results = new ArrayList<>();

        response.hits().hits().forEach(hit -> {

            Map<String, Object> item = new LinkedHashMap<>();

            item.put("id", hit.id());
            item.put("score", hit.score());
            item.put("source", hit.source());

            results.add(item);
        });

        long total = response.hits().total() != null
            ? response.hits().total().value()
            : results.size();

        return Map.of(
            "query", q,
            "total", total,
            "results", results
        );
    }
}
