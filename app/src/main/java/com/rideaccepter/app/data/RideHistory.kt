package com.rideaccepter.app.data

import android.content.Context
import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Room
import androidx.room.RoomDatabase
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "ride_history")
data class RideHistoryEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val appName: String,
    val fare: Double,
    val fareString: String,
    val pickupKm: Double?,
    val tripKm: Double?,
    val pickupLocation: String?,
    val dropoffLocation: String?,
    val timestamp: Long
)

@Dao
interface RideHistoryDao {
    @Insert
    suspend fun insertRide(ride: RideHistoryEntity)

    @Query("SELECT * FROM ride_history ORDER BY timestamp DESC")
    fun getAllRides(): Flow<List<RideHistoryEntity>>

    @Query("SELECT COALESCE(SUM(fare), 0) FROM ride_history")
    fun getTotalEarnings(): Flow<Double>

    @Query("DELETE FROM ride_history")
    suspend fun clearHistory()
}

@Database(entities = [RideHistoryEntity::class], version = 1, exportSchema = false)
abstract class RideDatabase : RoomDatabase() {
    abstract fun rideHistoryDao(): RideHistoryDao

    companion object {
        @Volatile private var INSTANCE: RideDatabase? = null
        fun get(context: Context): RideDatabase = INSTANCE ?: synchronized(this) {
            INSTANCE ?: Room.databaseBuilder(
                context.applicationContext, RideDatabase::class.java, "ride_history.db"
            ).build().also { INSTANCE = it }
        }
    }
}

class RideRepository(context: Context) {
    private val dao = RideDatabase.get(context).rideHistoryDao()
    val allRides: Flow<List<RideHistoryEntity>> = dao.getAllRides()
    val totalEarnings: Flow<Double> = dao.getTotalEarnings()
    suspend fun insert(ride: RideHistoryEntity) = dao.insertRide(ride)
    suspend fun clear() = dao.clearHistory()
}
