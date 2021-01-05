
import java.util.*;
import java.io.File;
import nl.uu.cs.ape.sat.APE;
import nl.uu.cs.ape.sat.models.Type;
import nl.uu.cs.ape.sat.models.logic.constructs.TaxonomyPredicate;
import nl.uu.cs.ape.sat.configuration.APEConfigException;
import nl.uu.cs.ape.sat.configuration.APECoreConfig;
import nl.uu.cs.ape.sat.utils.APEDimensionsException;
import nl.uu.cs.ape.sat.utils.APEDomainSetup;
import nl.uu.cs.ape.sat.configuration.APERunConfig;
import nl.uu.cs.ape.sat.models.AllTypes;

public class TestingWhatIsWrongWithAPE {
    public static void main(String args[]) throws Exception {
        System.out.println("Testing...");

        APECoreConfig config = new APECoreConfig(
              new File("../build/GISTaxonomy.rdf"),
              "http://geographicknowledge.de/vocab/CoreConceptData.rdf#",
              "http://geographicknowledge.de/vocab/GISTools.rdf#Tool",
              Arrays.asList("CoreConceptQ", "LayerA", "NominalA"),
              new File("../build/ToolDescription.json"),
              true
        );

        APE framework = new APE(config);

        APEDomainSetup domainSetup = framework.getDomainSetup();

        AllTypes domainTypes = domainSetup.getAllTypes();

        System.out.println(domainTypes.size());
    }
}
