plugins {
    id("org.jetbrains.kotlin.plugin.compose") version "2.3.20"
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "tw.edu.cgu.exchange_guide_flutter"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        isCoreLibraryDesugaringEnabled = true
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "tw.uniway.app"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = 24
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    buildTypes {
        release {
            val keyPath = System.getenv("UNIWAY_KEYSTORE")
            if (!keyPath.isNullOrBlank()) {
                signingConfig = signingConfigs.create("uniwayRelease") {
                    storeFile = file(keyPath)
                    storePassword = System.getenv("UNIWAY_STORE_PASSWORD")
                    keyAlias = System.getenv("UNIWAY_KEY_ALIAS") ?: "uniway-preview"
                    keyPassword = System.getenv("UNIWAY_KEY_PASSWORD")
                }
            }
        }
    }
    buildFeatures {
        compose = true
    }

}

gradle.taskGraph.whenReady {
    if (allTasks.any { it.name.contains("Release") } && System.getenv("UNIWAY_KEYSTORE").isNullOrBlank()) {
        throw GradleException("Release builds require UNIWAY_KEYSTORE and signing credentials; debug signing is not allowed.")
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}


dependencies {
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.4")
    implementation("androidx.glance:glance-appwidget:1.1.1")
}
