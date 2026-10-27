// Maintained natively: four independently selectable styles.

import WidgetKit
import SwiftUI

@main
struct StudyPlanWidgetDefinitionHomeWidgetBundle: WidgetBundle {
  var body: some Widget {
    StudyPlanWidgetDefinitionHomeWidget()
    CountdownWidget()
    ChecklistWidget()
    ProgressWidget()
  }
}
