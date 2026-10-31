import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// Every build is signed with the same key, so a newer APK installs over the older one and keeps the settings. The key
// in this folder is a plain "debug-style" key (password: android): it only proves "same app as before". Set the
// OFFICE_KEYSTORE_* variables (the GitHub workflow reads them from repository secrets) to sign with a private key instead.
val ownKey = System.getenv("OFFICE_KEYSTORE_FILE")

kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_17)
    }
}

android {
    namespace = "tw.uniway.office"
    compileSdk = 35

    defaultConfig {
        applicationId = "tw.uniway.office"
        minSdk = 26
        targetSdk = 35
        // The workflow passes the run number, which only ever goes up, so every build can update the one before it.
        versionCode = (findProperty("versionCode") as String?)?.toInt() ?: 1
        versionName = (findProperty("versionName") as String?) ?: "1.0.0"
    }

    signingConfigs {
        create("office") {
            storeFile = file(ownKey ?: "uniway-office.keystore")
            storePassword = System.getenv("OFFICE_KEYSTORE_PASSWORD") ?: "android"
            keyAlias = System.getenv("OFFICE_KEY_ALIAS") ?: "uniway-office"
            keyPassword = System.getenv("OFFICE_KEY_PASSWORD") ?: "android"
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("office")
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    lint {
        abortOnError = false
    }
}

dependencies {
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20240303") // the real org.json: android.jar's copy only has stubs on the JVM
}
