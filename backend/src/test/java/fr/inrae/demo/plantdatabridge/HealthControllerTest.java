package fr.inrae.demo.plantdatabridge;

import fr.inrae.demo.plantdatabridge.controller.HealthController;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class HealthControllerTest {

    @Test
    void healthReturnsOk() {
        HealthController controller = new HealthController();
        assertEquals("ok", controller.health().get("status"));
    }
}
